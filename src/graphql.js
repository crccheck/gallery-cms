// This might be a decent GraphQL client
// https://www.npmjs.com/package/@urql/preact

// TODO update url for production https://github.com/pikapkg/snowpack/issues/374
// For now, we'll assume that if we're connecting over port 8080, we're in dev mode
const GRAPHQL_URL = (location.port === '8080') ? `//${location.hostname}:8081/graphql` : '/graphql';

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
