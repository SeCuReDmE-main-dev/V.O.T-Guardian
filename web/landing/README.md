# V.O.T Guardian Landing

Static public pre-alpha landing for `vot-guardian.securedme.ca`.

Source-of-truth boundaries:

- V.O.T Guardian is supervised education and fraud-awareness only.
- Tenebris is represented as the real review/confidentiality boundary.
- Twilio is represented as a consent-first lane under implementation.
- Cactus is represented as a planned ephemeral/on-device inference capsule.
- Outputs are review artifacts requiring human review.

Local preview:

```powershell
$py = 'C:\Users\jeans\Desktop\Case study\modele\.venv\Scripts\python.exe'
& $py -m http.server 8784 --directory 'C:\Users\jeans\Desktop\Case study\modele\V.O.T-Guardian\web\landing'
```
