from nb_workflows import secrets

s1 = "gAAAAABiJUoYk63Q71KbuLjv7RmjdEuai8xEYGdo-FLRErgrTqfJW1zoM4SV_REJkqSSR22maQTEaqklolB1hbDQhE9mSmNxU8DZ9Le4WQv-wV6AbzJq661Hhg5aMvWA2usZxsXNbzJGJ-RpR9LS95CgNVzk6MzMQULaXS3UY8gsoNIN3rWZXTmc0UwT4retgIeWVNM1mftUqs97f2SO-qZR78pk4UnuX_piOuG7EnhmxHjX0h7PbXg="

line = "AGENT_EXAMPLE=gAAAAABiJUoYk63Q71KbuLjv7RmjdEuai8xEYGdo-FLRErgrTqfJW1zoM4SV_REJkqSSR22maQTEaqklolB1hbDQhE9mSmNxU8DZ9Le4WQv-wV6AbzJq661Hhg5aMvWA2usZxsXNbzJGJ-RpR9LS95CgNVzk6MzMQULaXS3UY8gsoNIN3rWZXTmc0UwT4retgIeWVNM1mftUqs97f2SO-qZR78pk4UnuX_piOuG7EnhmxHjX0h7PbXg=\n"


def test_secrets_parse_var_line():
    k, v = secrets._parse_var_line(line)

    assert k == "AGENT_EXAMPLE"
    assert v.endswith("=")
    assert v == s1


def test_secrets_open_vars_file():
    vars_ = secrets._open_vars_file("tests/test.nbvars")
    assert len(vars_.keys()) == 2
