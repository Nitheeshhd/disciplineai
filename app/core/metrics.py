from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "disciplineai_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "disciplineai_http_request_duration_seconds",
    "HTTP request duration seconds",
    ["method", "endpoint"],
)

habit_logged_events_total = Counter(
    "disciplineai_habit_logged_events_total",
    "Total habit logged domain events processed",
)
