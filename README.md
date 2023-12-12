# Shrinkify 2.0
Some advertisers experience a challenge with the character limits on Google Ads search creative headlines. 
This challenge directly affects their performance and scale, as they cannot use their full headlines in their ads, which leads to lower-quality search ads.

Shrinkify uses the VertexAI PaLM API to shorten long headlines to a certain number of characters in order to overcome this challenge and have better quality ads.

## Prerequisites

1. A new GCP project with billing attached

1. Upload your feed to BigQuery


## Installation

1. Click the big blue button to deploy:
   
   [![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

1. Choose your designated GCP project and desired region ().

1. Once installation is finished you will recieve your tool's URL. Save it.


## Usage

1. Enter industry and product type (i.e. Hotel booking, Hotel).

1. Choose the character limit you need (Important: It is recommended to use a slightly lower limit than you require. If you need a maximum of 30 chars, use a limit of 28)

1. Choose the dataset to which you uploaded your feed, and choose your feed.

1. Select relevant columns from the feed, from which Shrinkify will generate short titles. Select informative columns, where values vary between entries.

1. Click "Create Examples"

1. Shrinkify has randomly selected 5 entries from your feed. Add short titles for the examples and make sure the length is less then your selected characters limit.

1. Click "RUN"

1. Allow the tool some time to run. The final results feed with the short titles will be add to table called "shrinkify_final" in a dataset called "shrinkify_output".


## Costs

Costs are derived from GCP services usage and may vary dependaing on the frequancy of and the size of the feed.
The *approximate* cost is ~0.4$ per 1000 rows in your feed.

## Disclaimer
This is not an officially supported Google product.