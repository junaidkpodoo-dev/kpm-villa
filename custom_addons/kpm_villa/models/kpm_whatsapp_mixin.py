from odoo import models, fields, api, _
import requests
import logging

_logger = logging.getLogger(__name__)

class KpmWhatsappMixin(models.AbstractModel):
    _name = 'kpm.whatsapp.mixin'
    _description = 'WhatsApp Notification Mixin'

    def _clean_phone_number(self, phone):
        if not phone:
            return False
        # Remove all spaces, dashes, parentheses
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        if cleaned.startswith('00'):
            cleaned = '+' + cleaned[2:]
        
        # Default country code logic
        default_cc = self.env['ir.config_parameter'].sudo().get_param('kpm_villa.whatsapp_default_country_code', '91')
        if default_cc:
            if len(cleaned) == 10 and not cleaned.startswith(default_cc):
                cleaned = '+' + default_cc + cleaned
            elif not cleaned.startswith('+') and not cleaned.startswith(default_cc):
                cleaned = '+' + default_cc + cleaned
            elif not cleaned.startswith('+'):
                cleaned = '+' + cleaned
        else:
            if not cleaned.startswith('+'):
                cleaned = '+' + cleaned
        return cleaned

    def _send_whatsapp_message(self, partner_id, message):
        """
        Sends a WhatsApp message to the partner.
        Also posts the sent message to the chatter of the current record (if it inherits mail.thread)
        or the rent agreement chatter.
        """
        if not partner_id:
            return False
        
        phone = partner_id.mobile or partner_id.phone
        if not phone:
            log_msg = _("Failed to send WhatsApp message: Partner %s has no mobile or phone number configured.", partner_id.name)
            self._log_whatsapp_chatter(log_msg)
            return False
            
        cleaned_phone = self._clean_phone_number(phone)
        if not cleaned_phone:
            log_msg = _("Failed to send WhatsApp message: Invalid phone number for Partner %s.", partner_id.name)
            self._log_whatsapp_chatter(log_msg)
            return False

        config = self.env['ir.config_parameter'].sudo()
        api_url = config.get_param('kpm_villa.whatsapp_api_url')
        api_token = config.get_param('kpm_villa.whatsapp_api_token')
        phone_number_id = config.get_param('kpm_villa.whatsapp_phone_number_id')
        api_version = config.get_param('kpm_villa.whatsapp_api_version', 'v25.0')
        
        if not api_token:
            log_msg = _("Failed to send WhatsApp message: WhatsApp API Token is not configured in System Parameters (kpm_villa.whatsapp_api_token).")
            self._log_whatsapp_chatter(log_msg)
            return False

        if not api_url:
            if not phone_number_id:
                log_msg = _("Failed to send WhatsApp message: WhatsApp Phone Number ID is not configured in System Parameters (kpm_villa.whatsapp_phone_number_id).")
                self._log_whatsapp_chatter(log_msg)
                return False
            api_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': cleaned_phone.lstrip('+'),
            'type': 'text',
            'text': {
                'preview_url': False,
                'body': message,
            },
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                success_msg = _("WhatsApp Message Sent to %s (%s):\n\n%s", partner_id.name, cleaned_phone, message)
                print(success_msg)
                print("WhatsApp API Response:", response.text)
                self._log_whatsapp_chatter(success_msg)
                return True
            else:
                error_msg = _("WhatsApp Message Failed to send to %s (%s). API Response Code: %s. Response: %s", 
                              partner_id.name, cleaned_phone, response.status_code, response.text)
                self._log_whatsapp_chatter(error_msg)
                _logger.warning(error_msg)
                return False
        except requests.exceptions.ConnectionError as e:
            error_msg = _("WhatsApp Message Failed to send to %s (%s). Could not connect to API URL %s. Check the configured URL and server DNS/network access. Error: %s",
                          partner_id.name, cleaned_phone, api_url, str(e))
            self._log_whatsapp_chatter(error_msg)
            _logger.exception(error_msg)
            return False
        except requests.exceptions.Timeout as e:
            error_msg = _("WhatsApp Message Failed to send to %s (%s). API request timed out for URL %s. Error: %s",
                          partner_id.name, cleaned_phone, api_url, str(e))
            self._log_whatsapp_chatter(error_msg)
            _logger.exception(error_msg)
            return False
        except Exception as e:
            error_msg = _("WhatsApp Message Failed to send to %s (%s). Error: %s", partner_id.name, cleaned_phone, str(e))
            self._log_whatsapp_chatter(error_msg)
            _logger.exception(error_msg)
            return False

    def _send_whatsapp_template_message(self, partner_id, template_name, body_parameters=None, language_code='en', fallback_message=None):
        """
        Sends an approved WhatsApp Cloud API template message.
        Use this for business-initiated notifications outside the 24-hour customer service window.
        """
        if not partner_id:
            return False

        phone = partner_id.mobile or partner_id.phone
        if not phone:
            log_msg = _("Failed to send WhatsApp template: Partner %s has no mobile or phone number configured.", partner_id.name)
            self._log_whatsapp_chatter(log_msg)
            return False

        cleaned_phone = self._clean_phone_number(phone)
        if not cleaned_phone:
            log_msg = _("Failed to send WhatsApp template: Invalid phone number for Partner %s.", partner_id.name)
            self._log_whatsapp_chatter(log_msg)
            return False

        if not template_name:
            log_msg = _("Failed to send WhatsApp template: Template name is not configured.")
            self._log_whatsapp_chatter(log_msg)
            return False

        config = self.env['ir.config_parameter'].sudo()
        api_url = config.get_param('kpm_villa.whatsapp_api_url')
        api_token = config.get_param('kpm_villa.whatsapp_api_token')
        phone_number_id = config.get_param('kpm_villa.whatsapp_phone_number_id')
        api_version = config.get_param('kpm_villa.whatsapp_api_version', 'v25.0')

        if not api_token:
            log_msg = _("Failed to send WhatsApp template: WhatsApp API Token is not configured in System Parameters (kpm_villa.whatsapp_api_token).")
            self._log_whatsapp_chatter(log_msg)
            return False

        if not api_url:
            if not phone_number_id:
                log_msg = _("Failed to send WhatsApp template: WhatsApp Phone Number ID is not configured in System Parameters (kpm_villa.whatsapp_phone_number_id).")
                self._log_whatsapp_chatter(log_msg)
                return False
            api_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': cleaned_phone.lstrip('+'),
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': language_code},
            },
        }

        parameters = [{'type': 'text', 'text': str(value)} for value in (body_parameters or [])]
        if parameters:
            payload['template']['components'] = [{
                'type': 'body',
                'parameters': parameters,
            }]

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                success_msg = fallback_message or _("WhatsApp Template Sent to %s (%s): %s", partner_id.name, cleaned_phone, template_name)
                print(success_msg)
                print("WhatsApp Template API Response:", response.text)
                self._log_whatsapp_chatter(success_msg)
                return True

            error_msg = _("WhatsApp Template Failed to send to %s (%s). API Response Code: %s. Response: %s",
                          partner_id.name, cleaned_phone, response.status_code, response.text)
            self._log_whatsapp_chatter(error_msg)
            _logger.warning(error_msg)
            return False
        except requests.exceptions.ConnectionError as e:
            error_msg = _("WhatsApp Template Failed to send to %s (%s). Could not connect to API URL %s. Check the configured URL and server DNS/network access. Error: %s",
                          partner_id.name, cleaned_phone, api_url, str(e))
            self._log_whatsapp_chatter(error_msg)
            _logger.exception(error_msg)
            return False
        except requests.exceptions.Timeout as e:
            error_msg = _("WhatsApp Template Failed to send to %s (%s). API request timed out for URL %s. Error: %s",
                          partner_id.name, cleaned_phone, api_url, str(e))
            self._log_whatsapp_chatter(error_msg)
            _logger.exception(error_msg)
            return False
        except Exception as e:
            error_msg = _("WhatsApp Template Failed to send to %s (%s). Error: %s", partner_id.name, cleaned_phone, str(e))
            self._log_whatsapp_chatter(error_msg)
            _logger.exception(error_msg)
            return False

    def _log_whatsapp_chatter(self, message):
        """Logs the message to the current record's chatter if available, or the associated rent agreement chatter."""
        formatted_message = message.replace('\n', '<br/>')
        # 1. Try posting to the current record's chatter
        if hasattr(self, 'message_post'):
            try:
                self.message_post(body=formatted_message)
                return
            except Exception:
                pass
        
        # 2. Try posting to rent_id's chatter
        if hasattr(self, 'rent_id') and self.rent_id and hasattr(self.rent_id, 'message_post'):
            try:
                self.rent_id.message_post(body=formatted_message)
                return
            except Exception:
                pass

        # 3. Try posting to water_bill_id's chatter or other parents
        if hasattr(self, 'water_bill_id') and self.water_bill_id and hasattr(self.water_bill_id, 'message_post'):
            try:
                self.water_bill_id.message_post(body=formatted_message)
                return
            except Exception:
                pass
