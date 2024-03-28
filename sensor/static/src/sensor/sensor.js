/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { WebsocketWorker } from "@bus/workers/websocket_worker";

export class Sensor extends Component {
    static template = "sensor.sensors";

    setup() {
        this.tmp = useState({})
        this.odo = useState({})
        this.fph = useState({})

        const websocketWorker = new WebsocketWorker();
        websocketWorker.websocketURL = "ws://localhost:8069/websocket/sensors";

        websocketWorker._onWebsocketMessage = (messageEv)=>{
            const data = JSON.parse(messageEv.data)

            if (data.name.localeCompare("Temperature") === 0) {
                this.tmp.name =  data.name;
                this.tmp.value =  data.value;
            } else if (data.name.localeCompare("Dissolved oxygen") === 0) {
                this.odo.name = data.name;
                this.odo.value =  data.value;
            } else {
                this.fph.name = data.name;
                this.fph.value =  data.value;
            }            
        };

        websocketWorker._start();
    }
}
