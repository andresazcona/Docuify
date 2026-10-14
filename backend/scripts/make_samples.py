"""Generate the two sample PDFs in ../samples (a fictional employee handbook, in EN and ES).

python scripts/make_samples.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.pdfs import make_pdf  # noqa: E402

EN = [
    "Brightwave Labs - Employee Handbook\n\n"
    "Welcome to Brightwave Labs. This handbook explains how we work, what we expect from each "
    "other and what you can expect from the company. It applies to every employee and contractor.\n\n"
    "Working hours. Core hours are 10:00 to 15:00 in your local time zone. Outside core hours you "
    "choose your schedule, as long as your team can reach you for planned meetings.\n\n"
    "Remote work. Employees may work remotely up to three days per week. Managers must approve "
    "exceptions in writing. Fully remote contracts are available for roles marked as remote-first "
    "in the job description.",
    "Time off\n\n"
    "Vacation. Every employee receives twenty days of paid vacation per year. Unused days expire "
    "on March 31 of the following year. Vacation requests must be submitted at least two weeks in "
    "advance, except for emergencies.\n\n"
    "Sick leave. Employees receive ten paid sick days per year. A medical certificate is required "
    "after three consecutive days.\n\n"
    "Parental leave. The primary caregiver receives sixteen weeks of paid leave and the second "
    "caregiver receives eight weeks. Leave can be taken at any time during the first year.\n\n"
    "Public holidays. The company follows the public holidays of the country in your contract.",
    "Expenses and equipment\n\n"
    "Equipment. The company provides a laptop and a monitor to every employee. Equipment is "
    "replaced every four years or earlier if it fails. Return all equipment within ten days after "
    "leaving the company.\n\n"
    "Expenses. Submit receipts through the expense portal within thirty days. Travel must be "
    "booked through the approved agency. Meals while travelling are reimbursed up to fifty dollars "
    "per day.\n\n"
    "Learning budget. Each employee has an annual learning budget of one thousand dollars for "
    "courses, books and conferences. Unused budget does not roll over.\n\n"
    "Security. Use the company password manager and enable two-factor authentication on every work "
    "account. Report lost devices to the security team within one hour.",
]

ES = [
    "Brightwave Labs - Manual del empleado\n\n"
    "Bienvenido a Brightwave Labs. Este manual explica cómo trabajamos, qué esperamos unos de otros "
    "y qué puedes esperar de la empresa. Aplica a todos los empleados y contratistas.\n\n"
    "Horario. Las horas núcleo son de 10:00 a 15:00 en tu zona horaria. Fuera de ese horario "
    "eliges tu jornada, siempre que tu equipo pueda contactarte en las reuniones programadas.\n\n"
    "Trabajo remoto. Los empleados pueden trabajar de forma remota hasta tres días por semana. Los "
    "gerentes deben aprobar las excepciones por escrito. Los cargos marcados como remoto primero "
    "pueden tener contrato totalmente remoto.",
    "Tiempo libre\n\n"
    "Vacaciones. Cada empleado recibe veinte días de vacaciones pagadas al año. Los días no usados "
    "vencen el 31 de marzo del año siguiente. Las solicitudes se envían con al menos dos semanas de "
    "anticipación, salvo emergencias.\n\n"
    "Incapacidad. Los empleados reciben diez días de incapacidad pagada al año. Se exige "
    "certificado médico a partir del tercer día consecutivo.\n\n"
    "Licencia parental. La persona cuidadora principal recibe dieciséis semanas de licencia pagada "
    "y la segunda persona cuidadora recibe ocho semanas. Se puede tomar durante el primer año.",
    "Gastos y equipos\n\n"
    "Equipos. La empresa entrega un portátil y un monitor a cada empleado. Los equipos se renuevan "
    "cada cuatro años o antes si fallan. Todo el equipo se devuelve dentro de los diez días "
    "siguientes a la salida.\n\n"
    "Gastos. Los recibos se envían por el portal de gastos dentro de treinta días. Los viajes se "
    "reservan con la agencia aprobada. Las comidas en viaje se reembolsan hasta cincuenta dólares "
    "por día.\n\n"
    "Presupuesto de formación. Cada empleado tiene un presupuesto anual de mil dólares para cursos, "
    "libros y conferencias. El saldo no usado no se acumula.\n\n"
    "Seguridad. Usa el gestor de contraseñas de la empresa y activa la verificación en dos pasos en "
    "cada cuenta de trabajo. Reporta los dispositivos perdidos al equipo de seguridad en una hora.",
]

if __name__ == "__main__":
    out = ROOT.parent / "samples"
    out.mkdir(exist_ok=True)
    (out / "employee-handbook-en.pdf").write_bytes(make_pdf(EN))
    (out / "manual-del-empleado-es.pdf").write_bytes(make_pdf(ES))
    print(f"wrote {out}")
