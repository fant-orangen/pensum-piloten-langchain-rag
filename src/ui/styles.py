"""Shared UI styling for the Gradio frontend."""

BASE_UI_CSS = """
html,
body {
    width: 100%;
    min-height: 100%;
    margin: 0;
    padding: 0;
}

body {
    overflow-x: hidden;
}

gradio-app,
.gradio-container {
    width: 100%;
    min-height: 100vh;
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-container {
    max-width: none !important;
}

.gradio-container .main {
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
"""

AB_PAGE_CSS = """
.answer-box {
    min-height: 340px;
    max-height: 340px;
    overflow-y: auto;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 12px;
    background: #ffffff;
}

#chat-references-panel {
    max-height: 700px;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
    padding-right: 6px;
}

#chat-references-panel > div {
    max-width: 100%;
}
"""

CHAT_PAGE_CSS = """
#chat-page {
    padding: 0 0 1rem;
}

#chat-page-layout {
    gap: 1.25rem;
    align-items: stretch;
}

#chat-sidebar-column,
#chat-main-column {
    min-width: 0;
}

#chat-sidebar-column {
    display: flex;
}

.chat-shell-card {
    border: 1px solid #e9dccd;
    border-radius: 20px;
    background: linear-gradient(180deg, #fffdfa 0%, #fff6ee 100%);
    box-shadow: 0 18px 40px rgba(107, 76, 34, 0.08);
}

.chat-shell-card > .gr-block,
.chat-shell-card > div {
    gap: 0.9rem;
}

.chat-panel-title h2,
.chat-panel-title h3,
.chat-course-title h1,
.chat-course-title h2,
.chat-course-title h3 {
    margin-bottom: 0;
}

.chat-muted-text p {
    color: #6b7280;
}

.chat-page-toolbar {
    align-items: flex-start;
    gap: 1rem;
    justify-content: space-between;
}

.chat-page-toolbar > div:last-child {
    display: flex;
    justify-content: flex-end;
}

.chat-status-text p {
    margin-bottom: 0;
}

.chat-main-status {
    padding: 0 0.25rem;
}

#chat-sidebar-controls > .gr-block,
#chat-sidebar-controls > div,
#chat-sidebar-list-section > .gr-block,
#chat-sidebar-list-section > div {
    min-height: 0;
}

#chat-sidebar-shell,
.chat-sidebar-panel {
    height: 100%;
    min-height: 0;
}

#chat-sidebar-shell > .gr-block,
#chat-sidebar-shell > div {
    height: 100%;
    min-height: 0;
}

.chat-sidebar-list-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-height: 0;
    max-height: 44rem;
}

#chat-mode-selector,
#chat-mode-selector > .gr-block,
#chat-mode-selector > div {
    max-width: 100%;
    width: 100%;
}

#chat-mode-selector button,
#chat-mode-selector input {
    min-height: 48px;
}

#chat-conversation-selector > label,
#chat-conversation-selector legend {
    display: none !important;
}

#chat-sidebar-list-container {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow-x: hidden;
    overflow-y: auto;
    box-sizing: border-box;
    padding-right: 6px;
}

#chat-sidebar-list-container > .gr-block,
#chat-sidebar-list-container > div {
    min-height: 0;
    max-width: 100%;
}

#chat-conversation-selector,
#chat-conversation-selector > .gr-block,
#chat-conversation-selector > div {
    min-height: 0;
    max-width: 100%;
    width: 100%;
}

#chat-conversation-selector .wrap,
#chat-conversation-selector fieldset {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-width: 0;
    width: 100%;
}

#chat-conversation-selector .wrap > label,
#chat-conversation-selector fieldset > label {
    max-width: 100%;
    width: 100%;
}

#chat-conversation-selector .wrap {
    overflow: visible;
}

.chat-conversation-summary {
    padding-top: 0.25rem;
    border-top: 1px solid rgba(233, 220, 205, 0.9);
}

#chat-workspace {
    gap: 1rem;
    align-items: stretch;
    flex-wrap: nowrap;
}

.chat-workspace-panel {
    height: 100%;
}

.chat-workspace-panel > .gr-block,
.chat-workspace-panel > div {
    gap: 0.9rem;
}

#chat-main-actions {
    gap: 0.75rem;
}

#chat-main-actions > button {
    min-height: 48px;
}

#chat-main-actions > button:first-child {
    flex: 1.2;
}

#chat-main-actions > button:last-child {
    flex: 0.8;
}

#chat-message-composer textarea {
    min-height: 96px;
}

#chat-message-composer {
    border-radius: 16px;
}

#chat-open-references-button,
#chat-close-references-button {
    min-height: 46px;
}

#chat-chat-column,
#chat-references-column {
    min-width: 0;
}

#chat-chat-column {
    flex: 1 1 0 !important;
}

#chat-references-column {
    flex: 0 0 clamp(20rem, 28vw, 28rem) !important;
    max-width: clamp(20rem, 28vw, 28rem);
}

.chat-references-surface {
    height: 100%;
    min-height: 0;
    border: 1px solid #eadac6;
    border-radius: 24px;
    background: linear-gradient(180deg, #fffdfa 0%, #fff6ee 100%);
    box-shadow: 0 18px 40px rgba(107, 76, 34, 0.08);
}

.chat-references-surface > .gr-block,
.chat-references-surface > div {
    height: 100%;
    gap: 0.9rem;
}

.chat-references-header {
    align-items: center;
    gap: 0.75rem;
}

.chat-references-title h3 {
    margin-bottom: 0;
}

#chat-references-panel {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
    padding-right: 6px;
}

#chat-references-panel > div {
    max-width: 100%;
}

.chat-reference-panel {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.chat-reference-entry {
    border: 1px solid #eadac6;
    border-radius: 16px;
    background: linear-gradient(180deg, #ffffff 0%, #fffaf4 100%);
    overflow: hidden;
}

.chat-reference-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    cursor: pointer;
    list-style: none;
    font-weight: 600;
}

.chat-reference-summary::-webkit-details-marker {
    display: none;
}

.chat-reference-document {
    min-width: 0;
    word-break: break-word;
}

.chat-reference-page {
    flex-shrink: 0;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    background: #fff0df;
    color: #9a4f00;
    font-size: 0.85rem;
}

.chat-reference-body {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0 1rem 1rem;
    border-top: 1px solid #f1e6da;
}

.chat-reference-meta {
    display: grid;
    gap: 0.35rem;
    padding-top: 0.85rem;
    color: #4b5563;
}

.chat-reference-excerpt {
    padding: 0.9rem 1rem;
    border-radius: 14px;
    background: #fff7ed;
    line-height: 1.5;
    color: #1f2937;
    word-break: break-word;
}

@media (max-width: 1100px) {
    #chat-page-layout {
        flex-wrap: wrap;
    }

    #chat-sidebar-column {
        display: block;
    }

    #chat-workspace {
        flex-wrap: wrap;
    }

    #chat-chat-column,
    #chat-references-column {
        flex: 1 1 100% !important;
        max-width: 100%;
    }

    .chat-references-surface {
        height: auto;
    }

    #chat-sidebar-shell,
    .chat-sidebar-panel {
        height: auto;
    }

    .chat-sidebar-list-section {
        max-height: none;
    }

    #chat-sidebar-list-container {
        max-height: 20rem;
    }

    #chat-references-panel {
        max-height: 24rem;
    }

    .chat-reference-summary {
        align-items: flex-start;
        flex-direction: column;
    }
}
"""

TEACHER_PAGE_CSS = """
.teacher-course-nav .wrap {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}

.teacher-course-nav .wrap label {
    position: relative;
    width: 100%;
    min-height: 92px;
    margin: 0;
    padding: 18px 20px 44px;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    background: #ffffff;
    transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
}

.teacher-course-nav .wrap label:hover {
    border-color: #fb923c;
    box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.15);
}

.teacher-course-nav .wrap label:has(input:checked) {
    border-color: #f97316;
    background: #fff7ed;
    box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.22);
}

.teacher-course-nav .wrap label input,
.teacher-course-nav .wrap label .gradio-radio,
.teacher-course-nav .wrap label .radio-item-circle {
    display: none !important;
}

.teacher-course-nav .wrap label span {
    display: block;
    width: 100%;
    padding-right: 0;
    font-weight: 600;
}

.teacher-course-nav .wrap label::after {
    content: "Åpne";
    position: absolute;
    bottom: 16px;
    left: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #9a3412;
}

@media (max-width: 1100px) {
    .teacher-course-nav .wrap {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 720px) {
    .teacher-course-nav .wrap {
        grid-template-columns: minmax(0, 1fr);
    }
}
"""

APP_CSS = "\n".join((BASE_UI_CSS, AB_PAGE_CSS, CHAT_PAGE_CSS, TEACHER_PAGE_CSS))
