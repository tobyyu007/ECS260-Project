const { GraphQLClient } = require("graphql-request");
const fs = require("fs");
const fsPromises = require('fs').promises;
const path = require('path');
const argv = require("minimist")(process.argv.slice(2));
const fileName = argv.filename || "results";
const csv = require("csv-writer").createObjectCsvWriter;

const MAXRESULTS = 1000; // This is the maximum number of results GitHub can provide from a query. If the query returns more than this number, the date range will be split into smaller batches.
const REQUEST_TIMEOUT = 100; // Set the request timeout in milliseconds

// Add as many tokens as needed, considering the amount of data

const tokens = [
  "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",
];

let tokenIndex = 0;

// Function to check and delete file if it exists
function checkAndDeleteFile(filePath) {
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
    console.log(`Deleted existing file: ${filePath}`);
  }
}

// File paths
const jsonFilePath = path.join(__dirname, `${fileName}.json`);
const csvFilePath = path.join(__dirname, `${fileName}.csv`);
const incompleteDatesFilePath = path.join(__dirname, `${fileName} incomplete_dates.txt`);

// Check and delete files
checkAndDeleteFile(jsonFilePath);
checkAndDeleteFile(csvFilePath);
checkAndDeleteFile(incompleteDatesFilePath);

// Rotate through the available tokens and prevent rate limits or other restrictions that may be imposed on a single token.
function getNextToken() {
  const token = tokens[tokenIndex];
  tokenIndex = (tokenIndex + 1) % tokens.length;
  return token;
}

const batchSize = argv.batchsize || 10; // Set the desired batch size. Maximum is 100

// Fecth a batch of results based on the provided search query, current date, cursor (pagination), and previous results. 
async function fetchResultsBatch(searchQuery, currentDate, cursor = null, results = []) {
  try {
    const client = new GraphQLClient("https://api.github.com/graphql", {
      headers: {
        Authorization: `Bearer ${getNextToken()}`
      }
    });

    const data = await client.request(query, {
      searchQuery,
      first: batchSize,
      after: cursor
    });

    const { nodes, pageInfo } = data.search;
    results.push(...nodes);
    if (currentDate !== undefined) {
      console.log(`Extracted ${results.length} results for ${currentDate}..`);
    } else {
      console.log(`Extracted ${results.length} results so far..`);
    }

    const rateLimitData = await client.request(rateLimitQuery);
    const rateLimit = rateLimitData.rateLimit;
    // console.log("Rate Limit:", rateLimit);
    // console.log("hasNextPage:", pageInfo.hasNextPage);
    // console.log("endCursor:", pageInfo.endCursor);

    if (pageInfo.hasNextPage) {
      // Delay between batches to avoid rate limits
      await new Promise((resolve) => setTimeout(resolve, REQUEST_TIMEOUT)); // Adjust the delay time as needed
      return await fetchResultsBatch(searchQuery, currentDate, pageInfo.endCursor, results);
    } else {
      return results;
    }
  } catch (error) {
    console.error(error);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function resultsInDateRange(completeSearchQuery, currentStartDate, nextEndDate) {
  console.log("Checking if date range should split: " + currentStartDate + ".." + nextEndDate);
  while (true) { // Infinite loop, will break out on success or manual interruption
    try {
      const client = new GraphQLClient("https://api.github.com/graphql", {
        headers: {
          Authorization: `Bearer ${getNextToken()}`
        }
      });
      let data = await client.request(countQuery, { completeSearchQuery });
      const { repositoryCount } = data.search;
      console.log(`Total results in this time range: ${repositoryCount}`);
      return repositoryCount;
    } catch (error) {
      console.error(error);
      console.log("GraphQL Fetching Error Occurred, Retrying in 1 minute...");
      await sleep(60000); // Wait for 1 minute (60000 milliseconds)
    }
  }
}

// Determine whether to fetch all results in a single batch or in multiple batches based on total results and dates.
async function fetchAllResults() {
  try {
    const client = new GraphQLClient("https://api.github.com/graphql", {
      headers: {
        Authorization: `Bearer ${getNextToken()}`
      }
    });

    const data = await client.request(countQuery, { completeSearchQuery });
    const { repositoryCount } = data.search;
    console.log(`Total results for this query: ${repositoryCount}`);
    console.log("==============================================================")

    if (repositoryCount <= MAXRESULTS) {
      return fetchResultsBatch(completeSearchQuery);
    } else {
      let startDateObj = new Date(startDate);
      let endDateObj = new Date(endDate);

      const dayInMilliseconds = 24 * 60 * 60 * 1000;
      let dayCount = Math.ceil((endDateObj - startDateObj) / dayInMilliseconds);
      //    console.log(dayCount);
      let results = [];

      //keep dividing the search query into smaller batches based on the date range
      let currentStartDateObj = startDateObj;
      let currentStartDate = startDate;
      let nextEndDateObj = new Date(currentStartDateObj.getTime() + dayInMilliseconds * dayCount / 2);
      let nextEndDate = nextEndDateObj.toISOString().split("T")[0];

      while (nextEndDate <= endDate) {
        let nextSearchQuery = `${searchQuery} ${dateType}:${currentStartDate}..${nextEndDate}`;
        let nextResultCount = await resultsInDateRange(nextSearchQuery, currentStartDate, nextEndDate);

        // Check if nextEndDate is not progressing
        if (currentStartDate === nextEndDate && nextResultCount > MAXRESULTS) {
            console.log(`Warning: result count exceeds ${MAXRESULTS}. Recording this date.`);
            try {
              await fsPromises.appendFile(`${fileName} incomplete_dates.txt`, currentStartDate + ",", null, 2);
            } catch (err) {
              console.error(`Error writing to ${fileName} incomplete_dates.txt`, err);
            }

            let result = await fetchResultsBatch(nextSearchQuery, currentStartDate + ".." + nextEndDate);
            await writeFiles(result, writeJSON=false, writeCSV=true);
            results.push(...result);
  
            currentStartDateObj = new Date(nextEndDateObj.getTime() + dayInMilliseconds);
            currentStartDate = currentStartDateObj.toISOString().split("T")[0];
            if (currentStartDate > endDate) break;
            nextEndDateObj = endDateObj;
            nextEndDate = nextEndDateObj.toISOString().split("T")[0];
        }

        if (nextResultCount === null) {
          console.log("Error: No results found.");
          return null;
        }
        if (nextResultCount <= MAXRESULTS) {

          if (nextResultCount > 0) {
            let result = await fetchResultsBatch(nextSearchQuery, currentStartDate + ".." + nextEndDate);
            await writeFiles(result, writeJSON=false, writeCSV=true);
            results.push(...result);
          }

          currentStartDateObj = new Date(nextEndDateObj.getTime() + dayInMilliseconds);
          currentStartDate = currentStartDateObj.toISOString().split("T")[0];
          if (currentStartDate > endDate) break;
          nextEndDateObj = endDateObj;
          nextEndDate = nextEndDateObj.toISOString().split("T")[0];
        }
        else {
          dayCount = Math.ceil((nextEndDateObj - currentStartDateObj) / dayInMilliseconds);
          //console.log(`\nSplitting ${currentStartDate}..${nextEndDate} into ${dayCount} days...`);
          if (dayCount == 1)
            nextEndDateObj = new Date(currentStartDateObj.getTime());
          else
            nextEndDateObj = new Date(currentStartDateObj.getTime() + dayInMilliseconds * dayCount / 2);
          
          nextEndDate = nextEndDateObj.toISOString().split("T")[0];
        }
      }
      
      return results;
    }
  } catch (error) {
    console.error(error);
  }
}

// Write formatted data in JSON and CSV files
async function writeFiles(json, writeJSON, writeCSV) {
  if (!json || json.length === 0) {
    console.log('No data to write.');
    return;
  }

  const formattedResults = json.map((result) => {
    // Modify according to the desired format and extraction fields
    const data = {
      name: result.nameWithOwner.split("/")[1],
      owner: result.nameWithOwner.split("/")[0],
      description: result.description ? result.description : "",
      url: result.url,
      createdAt: result.createdAt.split("T")[0],
      users: result.assignableUsers.totalCount,
      watchers: result.watchers.totalCount,
      stars: result.stargazerCount,
      forks: result.forkCount,
      projects: result.projects.totalCount,
      issues: result.issues.totalCount,
      pullRequests: result.pullRequests.totalCount,
      diskUsage: result.diskUsage,
      license: result.licenseInfo ? result.licenseInfo.spdxId : "",
      languages: result.languages.edges.map((edge) => edge.node.name),
      primaryLanguage: result.primaryLanguage ? result.primaryLanguage.name : "",
      environments: result.environments.edges.map((edge) => edge.node.name),
      submodules: result.submodules.edges.map((edge) => edge.node.name),
      topics: result.repositoryTopics.edges.map((edge) => edge.node.topic.name),
    };

    // Check if the dictionary file exists
    if (fs.existsSync("dictionary.json")) {
      // Read the dictionary file
      const dictionary = require("./dictionary.json");

      // Escape special characters in the tag for regular expression
      const escapeRegExp = (string) => {
        return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      };

      // Check if any word in the name or description matches the tag from the dictionary
      const isTagInNameOrDescription = (tag) => {
        const regexString = `\\b${escapeRegExp(tag)}\\b`;
        const regex = new RegExp(regexString, "i");

        // Check if the tag is found as a whole word in the name or description
        return regex.test(data.name) || regex.test(data.description);
      };

      // Filter the dictionary tags based on word matching
      const nameAndDescTags = dictionary.filter((currentTag) => isTagInNameOrDescription(currentTag.tag));

      // Check if the tags are already in the topics field, and if not, add them to the 'extra' column
      const extraTags = nameAndDescTags.filter((currentTag) => {
        return !data.topics.includes(currentTag.tag);
      });

      data.extra = extraTags.map((currentTag) => currentTag.tag);
    }

    return data;
  });

  if(writeJSON){
    // Save as JSON
    try {
      await fsPromises.appendFile(`${fileName}.json`, JSON.stringify(formattedResults, null, 2));
      console.log(`${fileName}.json file updated`);
    } catch (err) {
      console.error(`Error writing to ${fileName}.json:`, err);
    }
  }

  if(writeCSV){
    // Save as CSV
    try {
      const csvWriter = csv({
        path: `${fileName}.csv`,
        header: Object.keys(formattedResults[0]).map((key) => ({ id: key, title: key })),
        append: true,
      });
      await csvWriter.writeRecords(formattedResults);
      console.log(`${fileName}.csv file updated\n`);
    } catch (err) {
      console.error(`Error writing to ${fileName}.csv:`, err);
    }
  }
}


// Write JSON file without any format or dictionary
// function writeJsonFile(json) {
//   fs.writeFile(`${fileName}.json`, JSON.stringify(json, null, 2), function (err) {
//     if (err) throw err;
//     console.log(`${fileName} file saved`);
//   });
// }

// Set query, count its totals and check rate limits
const query = `query ($searchQuery: String!, $first: Int, $after: String) {
  search(query: $searchQuery, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    nodes {
      ... on Repository {
        nameWithOwner
        description
        url
        createdAt
        assignableUsers {
          totalCount
        }
        watchers {
          totalCount
        }
        stargazerCount
        forkCount
        projects {
          totalCount
        }
        issues {
          totalCount
        }
        pullRequests {
          totalCount
        }
        diskUsage
        licenseInfo {
          spdxId
        }
        languages(first: 10) {
          edges {
            node {
              name
            }
          }
        }
        primaryLanguage {
          name
        }
        environments(first: 10) {
          edges {
            node {
              name
            }
          }
        }
        submodules(first: 10) {
          edges {
            node {
              name
            }
          }
        }
        repositoryTopics(first: 10) {
          edges {
            node {
              topic {
                name
              }
            }
          }
        }
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}`;

const countQuery = `query ($completeSearchQuery: String!) {
  search(query: $completeSearchQuery, type: REPOSITORY, first: 1) {
    repositoryCount
  }
}`;

const rateLimitQuery = `query {
  rateLimit {
    limit
    cost
    remaining
    used
    resetAt
    nodeCount
  }
}`;

// Create arguments and set defaults
const now = new Date().toISOString().split("T")[0];
const searchQuery = argv.query || "";
const startDate = argv.start || "2008-01-01";
const endDate = argv.end || now;
const dateType = argv.date || "created";

// Construct the search query with the date range
const completeSearchQuery = `${searchQuery} ${dateType}:${startDate}..${endDate}`;
console.log("==============================================================")
console.log("Search Query:", completeSearchQuery);

// Run and write the extraction
fetchAllResults()
  .then((data) => {
    writeFiles(data, writeJSON=true, writeCSV=false);
    console.log("==============================================================");
    console.log(`Saved ${data.length} results in total`);
    console.log("==============================================================");
  })
  .catch((error) => console.error(error));
