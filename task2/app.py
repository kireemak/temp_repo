from flask import Flask, request

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

resource = Resource(attributes={
    "service.name": "my-flask-app"
})

traceProvider = TracerProvider(resource=resource)
trace_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
traceProvider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(traceProvider)
tracer = trace.get_tracer(__name__)

metric_exporter = OTLPMetricExporter(endpoint="http://otel-collector:4318/v1/metrics")
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meterProvider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meterProvider)
meter = metrics.get_meter(__name__)

requests_counter = meter.create_counter(
    "requests.count",
    description="Total number of requests",
)

app = Flask(__name__)

FlaskInstrumentor().instrument_app(app)

@app.route("/")
def hello():
    requests_counter.add(1, {"endpoint": "/"})
    
    with tracer.start_as_current_span("hello-span") as span:
        name = request.args.get('name', 'World')
        span.set_attribute("user.name", name)
        return f"Hello, {name}!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)