# PrimeTrade Portfolio Presentation Assets

This document contains copy-pasteable materials and talking points for resumes, portfolios, and technical interviews based on the PrimeTrade codebase.

---

## 📄 Resume Bullet Points

### **Backend Software Engineer / Algorithmic Trading Developer**
- **Engineered** a modular, production-grade algorithmic trading bot in Python 3.13 for the Binance Futures Testnet (USDT-M) utilizing Clean Architecture and SOLID design principles.
- **Implemented** a pre-flight validation layer using regex validation patterns to local-check symbols, side constraints, and price/size rules, reducing API roundtrip latency and preventing invalid request submissions.
- **Designed** a robust, thread-safe logging framework using Loguru with 10 MB rotation and 7-day retention policies, logging raw payloads, latency times (ms), exceptions with tracebacks, and retry metrics.
- **Architected** an API client wrapper with exponential backoff retry mechanisms using `tenacity` to handle transient network issues and connection dropouts, maintaining system resilience.
- **Developed** a lightweight companion UI dashboard using Streamlit and Docker Compose, presenting account status metrics, order placement interfaces, and live tail logs for enhanced monitoring.
- **Authored** 14 automated unit tests using `pytest` to achieve 100% code coverage on data parsers, custom exception handlers, and pre-trade parameters checking.

---

## 💼 Technical Interview Q&A Guide

### **Q1: What architectural patterns did you follow when designing this trading bot?**
> **Answer**: "I followed a **Clean Architecture** style, separating input drivers, core business logic, and external system infrastructure. The CLI (`cli.py`) and Web Dashboard (`streamlit_app.py`) act as presentation controllers. They forward requests to `OrderService` (`bot/orders.py`), which acts as an orchestrator. The validator (`bot/validators.py`) enforces business rules locally. The actual API driver (`bot/client.py`) wraps `python-binance` and HTTP client logic, and `bot/response_parser.py` parses responses into clean Pydantic domain models. This separation ensures that if Binance changes its API schema, only the parser and client modules need modification, keeping the core validation and ordering orchestrator untouched."

### **Q2: Why did you implement a local validation layer instead of letting the exchange handle bad inputs?**
> **Answer**: "Local validation provides two primary advantages: **reliability** and **cost reduction**. Sending requests that are destined to fail (e.g., negative sizes, missing limit prices, invalid symbols) wastes network bandwidth and introduces API latency. More importantly, in real-world trading, sending frequent malformed requests can trigger Binance's rate-limiter or IP ban policies. Standardizing parameters check locally ensures we safeguard our IP reputation and reduce network overhead."

### **Q3: Tell me about a challenge you solved during this project.**
> **Answer**: "While setting up the Docker environment and testing against Python 3.13, we hit a build error where `pydantic-core` failed to compile its native Rust binding because the pinned PyO3 package did not support the Python 3.13 interpreter version. To solve this without compromising code safety, I updated our dependencies checklist to loosen Pydantic versions to `pydantic>=2.9.0` and `pydantic-settings>=2.6.0`, which ship with pre-compiled binary wheels for Python 3.13. This eliminated the compile-from-source requirement and reduced our Docker build duration from 5 minutes to 30 seconds."

---

## 📐 System Design Decisions

1. **Synchronous Core vs. Asynchronous CLI**:
   - *Decision*: We used synchronous calls wrapped inside `cli.py` and `streamlit_app.py`.
   - *Rationale*: For a single-user CLI bot executing trades sequentially, sync calls wrapped in robust timeouts are easier to reason about, simpler to debug, and eliminate asynchronous thread races.
2. **Pydantic Data Schemas**:
   - *Decision*: Adopted Pydantic for `OrderRequest` and `OrderResponse` objects.
   - *Rationale*: Pydantic enforces type constraints at runtime. It automatically converts string numbers returned by the Binance API into floats, guaranteeing type safety across the domain layer.
3. **Decoupled Logging Configuration**:
   - *Decision*: Avoided placing logger setups inside the client class; instead, structured a separate `bot/logger.py` utility.
   - *Rationale*: Allows easy adaptation. If the bot is deployed in a microservice framework (e.g., GCP Cloud Run, AWS ECS), the console handler can be formatted to output structured JSON logs for log ingestion tools like Datadog or ELK without changing the business logic.

---

## 🚀 Scalability & Future Roadmaps

If this bot were scaled up to support active mainnet high-frequency trading:
1. **Low-Latency Order Book Integration**:
   - *Implementation*: Replace HTTP polling with WebSockets to maintain a local order-book mirror, enabling sub-millisecond price referencing.
2. **Redis Message Queue**:
   - *Implementation*: Decouple signal generation from execution by sending signals to a Redis queue. Multiple worker bot containers can subscribe and fill orders concurrently.
3. **Hardware Isolation (Co-location)**:
   - *Implementation*: Deploy the bot containers in cloud servers situated in AWS Tokyo (ap-northeast-1) or Binance API co-located datacenters to minimize ping latency to <5ms.
