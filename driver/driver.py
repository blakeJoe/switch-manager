from oslo_utils import importutils


switch_type_map = {
    'huawei_s': 'driver.huawei.switch_s.SwitchS',
    'huawei_ce': 'driver.huawei.switch_ce.SwitchCE',
    'h3c_s': 'driver.h3c.h3c_s.H3CS'
}


def get_driver(switch_config):
    switch_name = switch_config.name
    if switch_name is None:
        raise Exception('switch_name is none!')

    m_ip = switch_config.m_ip
    switch_type = switch_config.switch_type
    username = switch_config.username
    password = switch_config.password
    if m_ip is None \
            or username is None \
            or password is None \
            or switch_type is None:
        raise Exception("switch info must specific!")

    driver = importutils.import_class(switch_type_map.get(switch_type))
    return driver(switch_config)
