/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Sensor } from "./sensor/sensor";

class SensorValue extends Component {}

SensorValue.components = { Sensor };
SensorValue.template = "sensor.sensor_value";

registry.category("actions").add("sensor.dashboard", SensorValue);