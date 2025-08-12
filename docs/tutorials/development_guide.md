# Development guide

Welcome to our developer contribution guidelines!

You should know that we would be glad to help you contribute to Ralph! Here's our [Discord](https://discord.gg/vYx6YWxJCS) to contact us easily.


## Preparation

!!! note "Prerequisites"
    Ralph development environment is containerized with Docker for consistency.
    Before diving in, ensure you have the following installed:

    - [Docker Engine](https://docs.docker.com/engine/install/)
    - [Docker Compose](https://docs.docker.com/compose/install/)
    - [make](https://www.gnu.org/software/make/manual/make.html)


!!! info
    In this tutorial, and even more generally in others tutorials, we tend to use Elasticsearch backend. Note that you can do the same with [another LRS backend](../features/backends.md) implemented in Ralph.

To start playing with `ralph`, you should first `bootstrap` using:

```bash
make bootstrap
```


When bootstrapping the project for the first time, the `env.dist` template file is copied to the `.env` file.
You may want to edit the generated `.env` file to set up available backend parameters that will be injected into the running container as environment variables to configure Ralph (see [backends documentation](../features/backends.md)):

```bash
# Elasticsearch backend
RALPH_BACKENDS__LRS__ES__HOSTS=http://elasticsearch:9200
RALPH_BACKENDS__LRS__ES__INDEX=statements
RALPH_BACKENDS__LRS__ES__TEST_HOSTS=http://elasticsearch:9200
RALPH_BACKENDS__LRS__ES__TEST_INDEX=test-index

# [...]
```

!!! info "Default configuration in `.env` file"

    Defaults are provided for some environment variables that you can use by uncommenting them.

## Backends

!!! tips "Virtual memory for Elasticsearch"
    In order to run the Elasticsearch backend locally on GNU/Linux operating
    systems, ensure that your virtual memory limits are not too low and increase
    them if needed by typing this command from your terminal (as
    `root` or using `sudo`):

    `sysctl -w vm.max_map_count=262144`

    Reference:
    https://www.elastic.co/guide/en/elasticsearch/reference/master/vm-max-map-count.html

!!! warning "Disk space for Elasticsearch"

    Ensure that you have at least **10%** of available disk space on your machine to run Elasticsearch. 

Once configured, start the database container using the following command, substituting `[BACKEND]` by the backend name (_e.g._ `es` for Elasticsearch):

```bash
make run-[BACKEND]
```

You can also start other services with the following commands:
```bash
make run-es
make run-mongo
# Start all backends
make run-all
```

Now that you have started the `elasticsearch` backend,
it's time to play with them with Ralph CLI:

We can now check that we have properly indexed the JSON file in Elasticsearch
```bash
bin/ralph read -b es
>>> {"id": 1, "foo": "bar"}
```

## After your development

### Testing

To run tests on your code, either use the `test` Make target or the
`bin/pytest` script to pass specific arguments to the test runner:

```bash
# Run all tests
make test

# Run pytest with options
bin/pytest -x -k mixins

# Run pytest with options and more debugging logs
bin/pytest tests/api -x -vvv -s --log-level=DEBUG -k mixins
```

### Linting

To lint your code, either use the `lint` meta target or one of the linting tools we use:

```bash
# Run all linters
make lint

# Run ruff linter
make lint-ruff

# Run ruff linter and resolve fixable errors
make lint-ruff-fix

# List available linters
make help | grep lint-
```

### Documentation

In case you need to document your code, use the following targets:

```bash
# Build documentation site
make docs-build

# Run mkdocs live server for dev docs
make docs-serve
```