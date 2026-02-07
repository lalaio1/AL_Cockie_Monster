# 🍪 AL Cookie Monster API

![ALCookieMonster](./logo.png)

Uma **API para análise, filtragem, validação e avaliação de risco de cookies HTTP**

---

## 🚀 Funcionalidades Principais

✅ Parse completo de cookies (Netscape / texto bruto)
✅ Análise de segurança (Secure, HttpOnly, SameSite, tracking, auth)
✅ Avaliação de risco com score e severidade
✅ Extração e análise de IPs embutidos em cookies
✅ Filtros avançados (session, persistent, tracking, insecure, etc.)
✅ Exportação (Netscape, JSON, CSV)
✅ Validação de estrutura e atributos
✅ Estatísticas completas
✅ Rate limit + headers de segurança
✅ Swagger UI integrado
✅ Backup automático do projeto

---



📍 API disponível em:

* `http://localhost:5000`

---

## 📡 Endpoints

### 🔍 `/api/analyze`

Analisa cookies e retorna relatório completo.

**Request (JSON):**

```json
{
  "cookies_text": "SESSIONID=abc123; Secure; HttpOnly"
}
```

**Response:**

```json
{
  "total_cookies": 1,
  "cookies": [...],
  "security_analysis": {...}
}
```

---

### ⚠️ `/api/risk-assessment`

Avaliação de risco com score e severidade.

🔴 critical | 🟠 high | 🟡 medium | 🟢 low

---

### 🧹 `/api/filter`

Filtra cookies por critérios.

```json
{
  "cookies_text": "...",
  "filters": {
    "secure": true,
    "session": false
  }
}
```

---

### 📤 `/api/export`

Exporta cookies filtrados.

Formatos:

* `netscape`
* `json`
* `csv`

---

### 🌍 `/api/ip-info`

Analisa IPs individualmente.

```json
{
  "ips": ["8.8.8.8", "1.1.1.1"]
}
```

---

### 🧠 `/api/extract-ips`

Extrai IPs diretamente dos cookies.

---

### 🔐 `/api/security-check`

Relatório de segurança (auth, tracking, flags inseguras).

---

### ✅ `/api/validate`

Validação estrutural de cookies.

---

### 📊 `/api/stats`

Estatísticas completas:

* por domínio
* por path
* por segurança
* session vs persistent

---

## 🛡️ Segurança

* Headers de segurança (CSP, HSTS, XSS Protection)
* Rate limit por IP
* Bypass automático para localhost
* Proteção contra abuso

---

## 🧪 Exemplo de Uso em Python

```python
import requests

resp = requests.post(
    "http://localhost:5000/api/analyze",
    json={"cookies_text": "SID=xyz; Secure; HttpOnly"}
)

print(resp.json())
```

---

