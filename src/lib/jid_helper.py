def parse_jid(jid_str: str):
    from neonize.proto.Neonize_pb2 import JID
    if "@" not in jid_str:
        return JID(
            User=jid_str,
            Device=0,
            Integrator=0,
            RawAgent=0,
            Server="s.whatsapp.net",
            IsEmpty=False
        )
    user_part, server = jid_str.split("@", 1)
    user = user_part
    device = 0
    raw_agent = 0
    if ":" in user_part:
        user_part, device_part = user_part.split(":", 1)
        user = user_part
        try:
            device = int(device_part)
        except ValueError:
            pass
    if "." in user:
        user_sub, agent_part = user.split(".", 1)
        user = user_sub
        try:
            raw_agent = int(agent_part)
        except ValueError:
            pass
    return JID(
        User=user,
        Device=device,
        RawAgent=raw_agent,
        Integrator=0,
        Server=server,
    )
