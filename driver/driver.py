from oslo_utils import importutils


subtype_map = {
    'huawei_s': 'driver.huawei.switch_s.SwitchS',
    'huawei_ce12804': 'driver.huawei.switch_ce.SwitchCE',
    'h3c_s6820': 'driver.h3c.h3c_s.H3CS'
}


def get_driver(switch_config):
    switch_name = switch_config.name
    if switch_name is None:
        raise Exception('switch_name is none!')

    m_ip = switch_config.m_ip
    username = switch_config.username
    password = switch_config.password
    sub_type = switch_name_analyze(switch_name)
    if m_ip is None \
            or username is None \
            or password is None \
            or sub_type is None:
        raise Exception("switch info must specific!")

    driver = importutils.import_class(subtype_map[sub_type])
    return driver(switch_config)


def switch_name_analyze(switch_name):
    if '6820' in switch_name:
        return 'h3c_s6820'
    elif '12804' in switch_name:
        return 'huawei_ce12804'
    else:
        return 'huawei_s'
