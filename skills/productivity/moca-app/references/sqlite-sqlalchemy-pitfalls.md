# SQLite + SQLAlchemy 2.x: armadilhas e padrões

## CHECK constraints
- Em CHECK, `NULL` conta como aprovado. Expressões que podem dar NULL (ex.: `json_type(col, '$.chave')` quando a chave não existe) precisam de `COALESCE(..., '') = 'valor'`, senão a restrição não bloqueia nada.
- Telefone só dígitos: `value NOT GLOB '*[^0-9]*' AND length(value) BETWEEN 10 AND 15`.
- JSON: `json_valid(col) AND json_type(col) = 'object'`.
- Combinações permitidas de colunas polimórficas: gere a CHECK a partir de um dict Python (fonte única) e valide o mesmo dict com `@validates` no ORM.

## Índices
- Unicidade de chave dentro de JSON: `Index("uq_x", text("json_extract(provenance, '$.idempotency_key')"), unique=True, sqlite_where=text("... IS NOT NULL"))` — índice parcial deixa documentos sem chave coexistirem.
- Use `MetaData(naming_convention=...)` desde o início: o Alembic em modo batch no SQLite precisa de nomes de constraint estáveis.

## Tipos
- SQLite não guarda fuso. Use um `TypeDecorator` que recusa datetime naive, grava UTC e devolve aware.
- Erros levantados dentro de `process_bind_param` chegam embrulhados em `sqlalchemy.exc.StatementError`; testes de "deve falhar" precisam capturar `StatementError` além de `IntegrityError`/`ValueError`.
- Enums: `SAEnum(PyEnum, native_enum=False, create_constraint=True, values_callable=lambda e: [m.value for m in e], name=...)` grava o VALOR e cria CHECK. Em Python 3.12 use `enum.StrEnum` (ruff UP042).
- `Uuid()` em SQLite vira CHAR(32) sem hífens; em JSON guarde UUID como string com hífens e nunca compare JSON com coluna em SQL.
- `group` é palavra reservada: o ORM cita automaticamente; não escreva SQL cru com essa tabela.

## Imutabilidade
- Trave colunas com `@event.listens_for(Model, "before_update")` + `inspect(target).attrs[c].history.has_changes()`; correção vira nova linha + vínculo `supersedes`.

## Conexão
- Listener `connect`: `PRAGMA foreign_keys=ON` (desligado por padrão no SQLite!), `journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`.
- Backup online: `sqlite3.Connection.backup()` + `PRAGMA integrity_check` na cópia.

## Ruff
- Com `target-version = "py312"` e regras `UP`, o `--fix` remove aspas de anotações `Mapped["X"]` (ok com `from __future__ import annotations`). Rode a validação do schema de novo depois do `--fix`.
