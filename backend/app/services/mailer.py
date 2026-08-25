from __future__ import annotations

import time
from typing import Any


async def send_mail(mail_options: dict[str, Any]) -> dict[str, str]:
    print(f"send through smtp (simulated): {mail_options.get('to')} subject: {mail_options.get('subject')}")
    return {"messageId": f"sim-{int(time.time() * 1000)}"}
