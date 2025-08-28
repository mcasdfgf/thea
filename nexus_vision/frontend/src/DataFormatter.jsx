/**
 * @file DataFormatter.jsx
 * @description
 * A component responsible for cleaning, parsing, and pretty-printing complex data objects.
 *
 * Its primary function, `unpackAllNestedStrings`, recursively traverses a data structure
 * and attempts to parse any string that looks like a JSON object or array. This is crucial
 * for handling the data from the .graphml file, where all attributes are stored as strings.
 * The component then uses `react-syntax-highlighter` to render the cleaned data with proper
 * JSON formatting and color coding.
 */

import React, { useMemo } from "react";
import SyntaxHighlighter from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";

export function unpackAllNestedStrings(data) {
  if (Array.isArray(data)) {
    return data.map((item) => unpackAllNestedStrings(item));
  }
  if (typeof data === "object" && data !== null) {
    return Object.fromEntries(
      Object.entries(data).map(([key, value]) => [
        key,
        unpackAllNestedStrings(value),
      ]),
    );
  }

  if (typeof data !== "string") {
    return data;
  }

  const trimmedData = data.trim();

  if (
    (trimmedData.startsWith("{") && trimmedData.endsWith("}")) ||
    (trimmedData.startsWith("[") && trimmedData.endsWith("]"))
  ) {
    try {
      const sanitizedStr = data
        .replace(/\\'/g, "'")
        .replace(/\\"/g, '"')
        .replace(/datetime\.datetime\(.*?\)/g, '"[DateTime Object]"')
        .replace(/np\.float64\((.*?)\)/g, "$1")
        .replace(/True/g, "true")
        .replace(/False/g, "false")
        .replace(/None/g, "null")
        .replace(/\(/g, "[")
        .replace(/\)/g, "]")
        .replace(/'/g, '"');

      const parsedData = JSON.parse(sanitizedStr);

      return unpackAllNestedStrings(parsedData);
    } catch (e) {
      return data;
    }
  }

  return data;
}

function DataFormatter({ data }) {
  const unpackedData = useMemo(() => unpackAllNestedStrings(data), [data]);

  return (
    <SyntaxHighlighter
      language="json"
      style={atomOneDark}
      customStyle={{
        background: "#1e1e1e",
        borderRadius: "5px",
        margin: 0,
        padding: "15px",
        textAlign: "left",
      }}
      wrapLines={true}
      wrapLongLines={true}
    >
      {JSON.stringify(unpackedData, null, 2)}
    </SyntaxHighlighter>
  );
}

export default DataFormatter;
