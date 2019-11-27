#!/usr/bin/python
# -*- coding: UTF-8 -*

from flask import Flask, jsonify
from flask import request
from switch import SwitchPool
from handler import HandlerPool

app = Flask(__name__)


@app.route('/api/shutdown_interfaces', methods=['POST'])
def shutdown_interfaces():
    sw = switch_pool.get_next_switch()
    if not isinstance(sw, str):
        hl = HandlerPool(sw)
        res, sd_intfs = hl.shutdown_interfaces()
        data = {
            'switch_name': sw.name,
            'switch_ip': sw.m_ip,
            'shutdown_interfaces': sd_intfs,
            'result': res,
        }
        return jsonify({'result': data}), 200
    else:
        return sw, 200


if __name__ == '__main__':
    switch_pool = SwitchPool()
    app.run(debug=True, host='0.0.0.0', port=8080)

