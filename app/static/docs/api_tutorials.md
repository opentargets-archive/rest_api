You can access any of the data at the base of targetvalidation.org via a REST API.
This is the same API that powers our website and gives full access to the
data that we use to build our search and visualizations.

The methods are divided in:
  - public -- the methods we will keep stable and support
  - private -- the methods we use to speed up the visualizations, but
  change often and thus should not be relied upon
  - utils -- miscellaneous methods useful for testing the status of the API
  - auth -- the calls one needs to validate an API token

Each of these method is described in detail on the [API documentation](), where each API call
can be tested using the [interactive interface](), powered by [swagger-ui](http://swagger.io/swagger-ui/).

## get an API token
If you are planning to do a large number of requests or are building an application
leveraging our API, you should [email us](mailto:support@targetvalidation.org) and obtain an API key.
Having a key will allow you to make more requests than an anonymous user and will also help us in the long term to
make the API better for you in the long term.
**We will never track the content of your API request** but instead monitor the overall usage of the API.

Also, don't forget to [let us know what you think](mailto:support@targetvalidation.org) of the API - we'd
love to hear how we could make the API more useful in our next release.


## Construct a query
Any REST API query is formed by a verb, an URL and a method.

[image of API call with labels]

## Interpret a response

The API will always offer a reponse in JSON format. Each response can be divided in headers and content.

[image of API response elements with labels]



## Get the data
There are a variety of ways of interacting with a REST API and the targetvalidation.org API in particular.

### Command line
From a unix/osx/cygwin command line the `curl` command is the easiest way to retrieve data from the API.

A typical curl is made up of the curl command, the -X option followed by the verb (usually GET or POST) and the query URL you have
constructed above.
If for instance we are interested in finding what the evidence linking BRAF and melanoma, the URL will look like:

     http://192.168.99.100:8008/api/latest/public/evidence/filter?target=braf&disease=melanoma

Pasting it in a browser window will show you a long json file. However a browser may not be
really useful. By using `curl` on the command line we can save the json and parse it. A more user-friendly alternative to curl is [httpie](https://github.com/jkbrzt/httpie)

An easy way to construct these queries is to head to our [interactive API interface](alpha.targetvalidation.org/api-docs), which allows
you to input parameters for each method and returns a response, as well as the
URL and curl equivalent of each call.


A tool such as [jq](http://jq.com) can be really useful in parsing json responses on the command line.
You can isolate specific fields by typing a `.` followed by the field name you want to filter
out from your json.

For instance:

You can also transform your json into a table:



### Python
Using python allows for better expressivity and may be a clearer way to parse the
resulting json. The standard way to access any REST API in python is by using
the `requests` library. After installing it via pip with `pip install requests`
you will be able to query the API:

    import requests
    r = requests.get(url,?)
    r.json

If for instance you are interested in evidence linking SOD1 and ALS you will write:




## Interpret a query


## Some examples of using the REST API

### Map a gene or diseaes of interest to ENSEMBL IDs or EFOs IDs
We leverage ensemble unique IDs to identify targets.

While you could use the ensembl API to obtain a list of IDs:

<snippet>

 you can also use our own API with the search method. For instance to search for
 the term associated with melanoma:

 <snippet>

 The same can be done for a given disease. One could query the EFO ontology directly through the [Ontology Lookup Service API](http://www.ebi.ac.uk/ols/beta/docs/api) but we recommend using our API directly, since the EFO version can sometimes diverge from the one used in our platform.

 <snippet>


### Retrieve a specific piece of evidence
0. find the IDs
 1. find all evidences using /public/evidence/filter
 2. isolate a specific evidence you care about using /public/evidence alone

### prioritize a gene list.

Given a gene list of interest, can we find out what is the ranking according to the evidence contained in targetvalidation.org ?
For each gene to disease connection we calculate an association score. Given a gene list and a particular disease of interest, we can
query the API to obtain the cumulative association score and rank the genes in the list based on it.


_optional_  First convert the gene list from their IDs to Ensembl IDs. One can save this script:

```sh
#!/usr/bin/env bash

# NOTE: this command does not run in parallel on purpose
# so that ordering of the gene IDs remains constant

while read gene; do
  curl -X GET http://rest.ensembl.org/xrefs/symbol/homo_sapiens/$gene?content-type=application/json 2>/dev/null | jq -r '.[0].id'
done < "${1:-/dev/stdin}"
#The substitution ${1:-...} takes $1 if defined otherwise the file name
# of the standard input of the own process is used.
```

as `gene2ensembl.sh` and run it from the command line feeding it the gene list of interest:

```sh
# make it executable
chmod u+x gene2ensembl.sh

# run in on the gene list for IBD
./gene2ensembl.sh genelist_ibd.txt > ensembl_list.txt
```

In parallel, one can query the targetvalidation.org API to get the list for IBD (EFO_0003767).
Using [httpie](http://httpie.org) and [jq](http://www.jq.org) the call becomes:
```
    http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' disease==EFO_0003767 datastructure==ids direct==false facets==false scorevalue_min==0 size==1000' | jq -r '.data[] | .target.symbol' > opentargets_ibd_list.txt
```

The resulting two lists can be intersected to isolate only those genes present in both.
For instance using `grep` we can obtain:

```
grep -f genelist_ibd.txt opentargets_ibd_list.txt > opentargets_top_ibd_genes.txt
```

an ordered list of common genes.


### Retrieve all targets involved in a particular disease category

To obtain association scores on all targets involved in a therapeutic area (eg. nervous system disease),
we query the API `/public/association/filter` method with the EFO ontology term (EFO_0000618 in this case).
Because the resulting list is longer than the maximum 1000 terms allowed, one can use
the `from` parameter to paginate a series of requests.
Again using [httpie](http://httpie.org) and [jq](http://www.jq.org) this becomes:


```sh
# First find out how many are there to begin with:

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 | jq '.total'
## which returns 5384

#Then paginate

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 | jq -r '.data[] | .target.symbol' > opentargets_neuro_list.txt

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 from==1000 | jq -r '.data[] | .target.symbol' >> opentargets_neuro_list.txt

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 from==2000 | jq -r '.data[] | .target.symbol' >> opentargets_neuro_list.txt

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 from==3000 | jq -r '.data[] | .target.symbol' >> opentargets_neuro_list.txt

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 from==4000 | jq -r '.data[] | .target.symbol' >> opentargets_neuro_list.txt

http 'https://alpha.targetvalidation.org/api/latest/public/association/filter' datastructure==ids size==1000 disease==EFO_0000618 direct==false scorevalue_min==0.2 from==5000 | jq -r '.data[] | .target.symbol' >> opentargets_neuro_list.txt

```
