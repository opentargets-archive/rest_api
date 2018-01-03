### The Open Targets Platform REST API

The Open Targets Platform API ('Application Programming Interface')
allows programmatic retrieval of our data via a set of
[REST](https://en.wikipedia.org/wiki/Representational_state_transfer)
services.

You can make calls to the latest version of our API using the base URL
 `https://api.opentargets.io/v3/platform`. Please make sure you use `https` instead of the unencrypted
 `http` calls, which we do not accept. Note that we only serve the latest version of the API. If you are interested in querying
 an old version, please [get in touch](mailto:support@targetvalidation.org) so that we can help.

We list below the methods available for you to query our data directly from the API. These methods will be
automatically generated from our Swagger UI. For every request you create, the interface will display a [curl](https://curl.haxx.se/) command
that you can copy and paste directly to a shell to obtain the same results without using an internet browser.

Check our [API blog posts](https://blog.opentargets.org/tag/api), for tutorials and additional
information on how to access of our data programmatically.

### Available Methods

The available methods can be grouped in four types:

* __public__ - Methods that serve the core set of our data. These are stable and we fully supported them.
* __private__ - Methods used by the web app to serve additional data not specific to our platform. These methods
may change without notice and should be used with caution.
* __utils__ - Methods to get statistics and technical data about our API.
* __auth__ - Methods used for authentication. These are only relevant if you have an API key (see the 'Fair Usage
and API keys' section below for more details).

### Supported formats

The four methods above are all available via a `GET` request, and will serve outputs as `JSON`.
Alternative output formats such `xml`, `csv` and `tab` are also available for some of the methods.
Please note that alternative output formats are not supported in this interactive page. The response here will always be in `json` format.

If you have complex queries with large number of parameters, you should
use a `POST` request instead of  `GET`. `POST` methods require a body encoded as `json`.
When querying for a specific disease using the latest version of the API, your call would look like the example below:

```sh
curl -X POST -d '{"disease":["EFO_0000253"]}' --header 'Content-Type: application/json' https://api.opentargets.io/v3/platform/public/evidence/filter
```
### How to interpret a response

Each HTTP response will serve data in headers and body.
The headers will give you details about your query, such as how long it took to run, and how much usage you have left (See the 'Fair Usage
and API keys' section below for more details).

In the body of the response, you will find the data you have requested for in a `json` format. The
[jq](https://stedolan.github.io/jq/) program is a useful tool to parse the json response while on the command line.

```sh
curl https://api.opentargets.io/v3/platform/public/association/filter\?target\=ENSG00000157764 | jq
```

We do not analyse the nature of any specific API queries except for the purposes of improving the performance of our API.
Read more in our [privacy section](https://www.targetvalidation.org/terms_of_use#privacy).

How can we make the Open Targets Platform API more useful to you? Would you like additional methods to be implemented?
Please [get in touch](mailto:support@targetvalidation.org) and send your suggestions.

### More examples
Check our [Getting started tutorial](https://blog.opentargets.org/api-getting-started-1) for more
examples on how to use the API and for some code snippets, which can be used to construct more complex queries.
