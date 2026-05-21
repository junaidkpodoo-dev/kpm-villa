/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class VillaDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            stats: {},
        });

        onWillStart(async () => {
            await this.loadStats();
        });
    }

    async loadStats() {
        const stats = await this.rpc("/villa/dashboard_stats");
        this.state.stats = stats;
    }
}

VillaDashboard.template = "kpm_villa.VillaDashboard";
registry.category("actions").add("villa_dashboard_tag", VillaDashboard);
