## Summary

-

## Type

- [ ] Parser or protocol fix
- [ ] CLI change
- [ ] Profile or vendor behavior
- [ ] Feature or API addition
- [ ] Documentation
- [ ] Packaging or CI

## Safety

- [ ] This change does not send SMS, place calls, delete messages, or alter modem audio settings in automated tests.
- [ ] Hardware-affecting behavior is documented and opt-in.
- [ ] Logs and fixtures redact phone numbers, IMSI, ICCID, IMEI, and SMS bodies.

## Validation

- [ ] `python scripts/check.py`
- [ ] Hardware smoke test, if relevant:
