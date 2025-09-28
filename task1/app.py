from flask import Flask, request

from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

resource = Resource(attributes={
    "service.name": "my-flask-app"
})

traceProvider = TracerProvider(resource=resource)

exporter = OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")

traceProvider.add_span_processor(BatchSpanProcessor(exporter))

trace.set_tracer_provider(traceProvider)

tracer = trace.get_tracer(__name__)

app = Flask(__name__)

FlaskInstrumentor().instrument_app(app)

@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span") as span:
        name = request.args.get('name', 'World')
        span.set_attribute("user.name", name)
        return f"Hello, {name}!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)