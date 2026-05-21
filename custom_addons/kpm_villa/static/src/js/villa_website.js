/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.VillaMobileApp = publicWidget.Widget.extend({
    selector: ".o_villa_app",
    events: {
        "click .btn-delete-agreement": "_onDeleteAgreement",
        "click .btn-add-due-payment": "_onAddDuePayment",
        "click .btn-add-new-payment": "_onAddNewPayment",
        "click .btn-add-water-payment": "_onAddWaterPayment",
    },

    _onAddDuePayment: function (ev) {
        const button = ev.currentTarget;
        const modal = document.querySelector("#addPaymentModal");
        if (!modal) return;

        modal.querySelector("#payment_id").value = button.dataset.paymentId || "";
        modal.querySelector("select[name='month']").value = button.dataset.paymentMonth || "";
        modal.querySelector("input[name='rent_amount']").value = button.dataset.paymentRent || "";
        modal.querySelector("#paid_amount").value = "";
        modal.querySelector("#paid_amount").max = button.dataset.paymentDue || "";
        modal.querySelector("#paid_amount_label").textContent = "Pay Due Amount";
        modal.querySelector("#addPaymentModalLabel").textContent = "Add Due Payment";
    },

    _onAddNewPayment: function (ev) {
        const button = ev.currentTarget;
        const modal = document.querySelector("#addPaymentModal");
        if (!modal) return;

        modal.querySelector("#payment_id").value = "";
        modal.querySelector("select[name='month']").value = button.dataset.paymentMonth || "";
        modal.querySelector("input[name='rent_amount']").value = button.dataset.paymentRent || "";
        modal.querySelector("#paid_amount").value = "";
        modal.querySelector("#paid_amount").removeAttribute("max");
        modal.querySelector("#paid_amount_label").textContent = "Paid Amount";
        modal.querySelector("#addPaymentModalLabel").textContent = "Add Payment";
    },

    _onAddWaterPayment: function (ev) {
        const button = ev.currentTarget;
        const modal = document.querySelector("#addWaterPaymentModal");
        if (!modal) return;

        modal.querySelector("#water_line_id").value = button.dataset.waterLineId || "";
        modal.querySelector("#water_payment_amount").value = "";
        modal.querySelector("#water_payment_amount").max = button.dataset.waterDue || "";
        modal.querySelector("#water_payment_note").textContent = `${button.dataset.waterName || "Water bill"} due: ${button.dataset.waterDue || "0"}`;
    },

    _onDeleteAgreement: async function (ev) {
        if (!confirm("Are you sure you want to delete this agreement?")) return;

        const agreementId = $(ev.currentTarget).data("id");
        const result = await this.rpc("/villa/mobile/agreement/delete", {
            agreement_id: agreementId,
        });

        if (result.status === "success") {
            $(ev.currentTarget).closest(".mobile-card").fadeOut();
        } else {
            alert("Error deleting record");
        }
    },
});