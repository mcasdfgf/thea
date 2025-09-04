/**
 * @file Modal.jsx
 * @description
 * A generic, reusable modal window component.
 *
 * It uses a React Portal to render its content at the top level of the DOM,
 * ensuring it appears above all other UI elements. The modal includes a backdrop,
 * a close button, and a "Copy" button to copy its structured data content to the clipboard.
 */

import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

function Modal({ isOpen, onClose, title, children, dataToCopy }) {
  const [copyText, setCopyText] = useState("Copy");

  useEffect(() => {
    if (isOpen) {
      setCopyText("Copy");
    }
  }, [isOpen]);

  const handleCopy = () => {
    const textToCopy = JSON.stringify(dataToCopy, null, 2);

    navigator.clipboard
      .writeText(textToCopy)
      .then(() => {
        setCopyText("Copied!");
        setTimeout(() => {
          setCopyText("Copy");
        }, 2000);
      })
      .catch((err) => {
        console.error("Failed to copy text: ", err);
        setCopyText("Error!");
        setTimeout(() => setCopyText("Copy"), 2000);
      });
  };

  if (!isOpen) {
    return null;
  }

  return ReactDOM.createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h4>{title}</h4>
          <div className="modal-actions">
            <button
              className={`modal-copy-button ${copyText === "Copied!" ? "copied" : ""}`}
              onClick={handleCopy}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              {copyText}
            </button>
            <button className="modal-close-button" onClick={onClose}>
              &times;
            </button>
          </div>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export default Modal;
