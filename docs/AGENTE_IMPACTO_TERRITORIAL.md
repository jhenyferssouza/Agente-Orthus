# Agente de Impacto Territorial — Issue #6

**Proprietário do projeto:** jhenyferssouza. **Responsável:** Marcioalexs. **Meta interna da Issue:** 25/11/2026.

## Finalidade e limitações

Este módulo é um PROTÓTIPO ACADÊMICO; todos os polígonos, ruas, setores, escolas, UBS e limites em `demo_data/` são FICTÍCIOS. Não usar em alertas reais, evacuação, segurança pública ou tomada de decisão operacional.

O agente transforma a saída do Agente #5 (níveis futuros relativos à MESMA estação/régua) em uma lista priorizada de zonas previamente mapeadas que alcançam um **limiar de referência demonstrativo**.

**Isso NÃO é modelagem hidráulica.** O instante de cruzamento de um limiar de nível em estação não representa a chegada da água em uma rua. O relatório informa `crossing_time_minutes`, mas marca `physical_water_arrival_time_available=false` e `external_public_alert_permitted=false`.

## Entradas

- `ForecastRequest`, fornecido pelo Agente #5 e pelo orquestrador #10.
- Catálogo territorial GeoJSON com `zones`, `sectors`, `streets` e `facilities`.
- Zonas ligadas a `station_id` e `threshold_level_cm`, com origem, unidade e documentação da correspondência hidrológica.

## Saídas

- Zonas ordenadas pelo primeiro cruzamento de limiar (proxy), com `zone_id`, bairro, ruas, equipamentos, população estimada e fonte.
- Total populacional agregado deduplicado pela união geométrica das zonas.
- Limitações e flags que impedem uso operacional.

## Validação e premissas

1. Não calcular áreas em graus de latitude/longitude. O script projeta os polígonos para EPSG:5880 (área equivalente), aproxima uma população distribuída uniformemente por setor e calcula fração de interseção. A população por área **não é contagem observada de pessoas atingidas**.
2. A relação da estação com as zonas só pode ser substituída por uma relação aprovada/calibrada; um sensor de distância medindo cm NÃO pode ser comparado diretamente a uma altitude em metros sem origem/datum vertical correspondente.
3. Mapas de suscetibilidade NÃO correspondem à mancha inundada prevista para uma cota específica. A integração futura deve usar manchas por cenário, perfis hidráulicos ou associação de limiares aprovada por especialista.
4. Dados incompletos ou estação desconhecida resultam em erro, não em certeza de segurança.
5. Dados sobre vulnerabilidades devem ser agregados e com acesso controlado. Não importar cadastros nominais no protótipo.

## Testes e execução

No Windows PowerShell, na raiz do repositório:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Testar-AgenteTerritorial.ps1
.\.venv\Scripts\python.exe -m uvicorn agents.territorial.api:app --reload --port 8006
```

Depois acesse `http://127.0.0.1:8006/docs` e execute `POST /territorial/analyze` com `forecast_demo.json`.

## Fontes públicas candidatas para substituir dados sintéticos

- SGB, carta de suscetibilidade de Campinas: https://rigeo.sgb.gov.br/items/8d04f349-ba43-483b-8100-d48c405808ce
- SGB, SIGs municipais: https://www.sgb.gov.br/sao-paulo-cartografia-de-suscetibilidade
- IBGE, Censo 2022 e agregados por setor: https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html?edicao=41852&t=downloads
- Prefeitura de Campinas, metadados espaciais: https://portal-adm.campinas.sp.gov.br/servico/consultar-metadados-espaciais
- SGB, camada de inundação, serviço de dados: https://geoportal.sgb.gov.br/server/rest/services/gestaoterritorial/inundacao/FeatureServer

Verificar licença, datum, resolução, área de cobertura, versão e se há relação calibrada com a régua/estação monitorada antes de ingestão. Equipamentos e ruas precisam de fonte e checagem geográfica. Nunca promover dados fictícios a dados operacionais.

## Integrações a negociar com colegas

- #5 (Previsão): `station_id`, `issued_at`, horizontes, níveis `level_cm`, unidade/referência, intervalos de incerteza.
- #7 (Comunicação): `affected_zones`, `critical_facilities`, `total_population_estimate`, `limitations` e `external_public_alert_permitted=false`.
- #8 (Locais seguros): zonas geográficas e ruas associadas. Não declarar rotas seguras a partir deste módulo.
- #10 (Orquestrador): rota `POST /territorial/analyze`, schema JSON, códigos HTTP e política de falha fechada.

## Pendências para cumprir integralmente a Issue #6

- Fornecer camada real de risco de enchente/área de inundação por cota e sua correspondência técnica com a estação.
- Acrescentar dados de altimetria com datum vertical compatível, verificados por especialista.
- Substituir dados demográficos fictícios por setores IBGE com população agregada e conferência de limites.
- Estimar fisicamente tempo de chegada da onda de cheia apenas quando houver modelo/medição de propagação validado. Até lá, relatório retorna proxy e não horário de chegada.
- Incorporar escolas/UBS georreferenciadas verificadas e cadastro de vulnerabilidade estritamente agregado/autorizado.
