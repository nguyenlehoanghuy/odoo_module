/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Tracking } from "./tracking/tracking";

class ObjectTracking extends Component {}

ObjectTracking.components = { Tracking };
ObjectTracking.template = "realtime_object_tracking.object_tracking";

registry.category("actions").add("realtime_object_tracking.dashboard", ObjectTracking);