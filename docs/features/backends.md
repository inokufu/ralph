# Backends for data storage

Ralph supports various backends that can be accessed to read from or write to (learning events or random data).
Implemented backends are listed below along with their configuration parameters. 
If your favourite data storage method is missing, feel free to submit your implementation or get in touch!

## Key concepts

Each backend has its own parameter requirements. These
parameters can be set as command line options or environment variables; the
later is the **recommended solution** for sensitive data such as service
credentials.

The general patterns for backend parameters are:

- `--{{ backend_name }}-{{ parameter | underscore_to_dash }}` for command options, and,
- `RALPH_BACKENDS__DATA__{{ backend_name | uppercase }}__{{ parameter | uppercase }}` for environment variables.

## Elasticsearch

Elasticsearch backend is mostly used for indexation purpose (as a datalake) but
it can also be used to fetch indexed data from it.

### ::: ralph.backends.data.es.ESDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## MongoDB

MongoDB backend is mostly used for indexation purpose (as a datalake) but
it can also be used to fetch collections of documents from it.

### ::: ralph.backends.data.mongo.MongoDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## File system

The file system backend is a dummy template that can be used to develop your own backend. 
It is a "dummy" backend as it is not intended for practical use (UNIX `ls` and `cat` would be more practical).

The only required parameter is the `path` we want to list or stream content from.

### ::: ralph.backends.data.fs.FSDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes
