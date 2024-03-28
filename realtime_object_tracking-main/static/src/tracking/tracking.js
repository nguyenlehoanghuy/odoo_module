/** @odoo-module **/

import { Component, useState} from "@odoo/owl";
import { WebsocketWorker } from "@bus/workers/websocket_worker";

export class Tracking extends Component {
    static template = "realtime_object_tracking.tracking";

    setup() {
        this.state = useState({
            img: "data:image/jpeg;base64,",
            object: "",
        });
        // this.img = document.createElement('img');
        // this.img.src = "data:image/jpeg;base64,";
        // document.body.appendChild(this.img);

        const websocketWorker = new WebsocketWorker();
        websocketWorker.websocketURL = "ws://localhost:8069/websocket/camera";

        websocketWorker._onWebsocketMessage = (messageEv)=>{
            const data = JSON.parse(messageEv.data)
            
            // Display the base64 image
            this.state.img = data.img;
            this.state.object = data.object;
            console.log(data);
        };

        websocketWorker._start();
    }
}
