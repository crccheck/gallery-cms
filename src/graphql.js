// This might be a decent GraphQL client
// https://www.npmjs.com/package/@urql/preact

const GRAPHQL_URL = `//${location.hostname}:8081/graphql`;

export async function query(query, variables) {
  const response = await fetch(GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, variables }),
  });
  return response.json();
}
