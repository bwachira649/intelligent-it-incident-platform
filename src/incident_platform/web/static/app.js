const API_BASE = "/api/v1";

const elements = {
    refreshButton: document.getElementById("refresh-button"),
    systemStatus: document.getElementById("system-status"),
    healthDot: document.getElementById("health-dot"),
    healthStatus: document.getElementById("health-status"),
    healthDescription: document.getElementById("health-description"),
    apiStatus: document.getElementById("api-status"),
    environmentStatus: document.getElementById("environment-status"),

    totalIncidents: document.getElementById("total-incidents"),
    openIncidents: document.getElementById("open-incidents"),
    acknowledgedIncidents: document.getElementById(
        "acknowledged-incidents"
    ),
    resolvedIncidents: document.getElementById("resolved-incidents"),

    lowIncidents: document.getElementById("low-incidents"),
    mediumIncidents: document.getElementById("medium-incidents"),
    highIncidents: document.getElementById("high-incidents"),
    criticalIncidents: document.getElementById("critical-incidents"),

    createIncidentForm: document.getElementById(
        "create-incident-form"
    ),
    createIncidentButton: document.getElementById(
        "create-incident-button"
    ),
    createIncidentStatus: document.getElementById(
        "create-incident-status"
    ),

    incidentsTableBody: document.getElementById(
        "incidents-table-body"
    ),
    incidentCount: document.getElementById("incident-count"),
    incidentDetails: document.getElementById(
        "incident-details"
    ),

    lastUpdated: document.getElementById("last-updated"),
    errorBanner: document.getElementById("error-banner"),
    errorMessage: document.getElementById("error-message"),
};

let selectedIncidentId = null;


async function fetchJson(url, options = {}) {
    const response = await fetch(
        url,
        options
    );

    if (!response.ok) {
        let detail =
            `API request failed with HTTP ${response.status}`;

        try {
            const errorData = await response.json();

            if (errorData.detail) {
                detail = errorData.detail;
            }
        } catch (error) {
            console.debug(
                "Unable to parse API error response.",
                error
            );
        }

        throw new Error(detail);
    }

    return response.json();
}


function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorBanner.classList.remove("hidden");
}


function clearError() {
    elements.errorBanner.classList.add("hidden");
    elements.errorMessage.textContent = "";
}


function setCreateIncidentStatus(message) {
    if (!elements.createIncidentStatus) {
        return;
    }

    elements.createIncidentStatus.textContent = message;
}


function setSystemHealthy(environment) {
    elements.systemStatus.textContent = "System healthy";

    elements.systemStatus.classList.remove(
        "unhealthy"
    );

    elements.systemStatus.classList.add(
        "healthy"
    );

    elements.healthDot.classList.remove(
        "unhealthy"
    );

    elements.healthDot.classList.add(
        "healthy"
    );

    elements.healthStatus.textContent = "Healthy";

    elements.healthDescription.textContent =
        "Incident platform API is responding normally.";

    elements.apiStatus.textContent = "Operational";

    elements.environmentStatus.textContent =
        environment || "Unknown";
}


function setSystemUnhealthy(message) {
    elements.systemStatus.textContent =
        "System unavailable";

    elements.systemStatus.classList.remove(
        "healthy"
    );

    elements.systemStatus.classList.add(
        "unhealthy"
    );

    elements.healthDot.classList.remove(
        "healthy"
    );

    elements.healthDot.classList.add(
        "unhealthy"
    );

    elements.healthStatus.textContent =
        "Unavailable";

    elements.healthDescription.textContent =
        message;

    elements.apiStatus.textContent =
        "Unavailable";

    elements.environmentStatus.textContent =
        "Unknown";
}


async function loadSystemHealth() {
    const health = await fetchJson("/health");

    if (health.status !== "healthy") {
        throw new Error(
            "API health check reported an unhealthy state."
        );
    }

    const root = await fetchJson("/");

    setSystemHealthy(root.environment);
}


async function loadStatistics() {
    const statistics = await fetchJson(
        `${API_BASE}/incidents/statistics`
    );

    elements.totalIncidents.textContent =
        statistics.total;

    elements.openIncidents.textContent =
        statistics.open;

    elements.acknowledgedIncidents.textContent =
        statistics.acknowledged;

    elements.resolvedIncidents.textContent =
        statistics.resolved;

    elements.lowIncidents.textContent =
        statistics.low;

    elements.mediumIncidents.textContent =
        statistics.medium;

    elements.highIncidents.textContent =
        statistics.high;

    elements.criticalIncidents.textContent =
        statistics.critical;
}


function formatDateTime(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}


function escapeHtml(value) {
    const text = String(value ?? "");

    return text
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function createBadge(value) {
    const normalized =
        String(value || "").toLowerCase();

    return `
        <span class="badge badge-${escapeHtml(normalized)}">
            ${escapeHtml(normalized)}
        </span>
    `;
}


function renderIncidents(incidents) {
    elements.incidentCount.textContent =
        incidents.length;

    if (incidents.length === 0) {
        elements.incidentsTableBody.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="table-message"
                >
                    No incidents found.
                </td>
            </tr>
        `;

        return;
    }

    elements.incidentsTableBody.innerHTML =
        incidents
            .map((incident) => {
                const selected =
                    incident.id === selectedIncidentId
                        ? "selected"
                        : "";

                return `
                    <tr
                        class="${selected}"
                        data-incident-id="${incident.id}"
                    >
                        <td>
                            <span class="incident-id">
                                #${incident.id}
                            </span>
                        </td>

                        <td>
                            <div class="incident-title">
                                ${escapeHtml(
                                    incident.title
                                )}
                            </div>

                            <div class="incident-description">
                                ${escapeHtml(
                                    incident.description
                                )}
                            </div>
                        </td>

                        <td>
                            ${createBadge(
                                incident.severity
                            )}
                        </td>

                        <td>
                            ${createBadge(
                                incident.status
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                incident.source
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                formatDateTime(
                                    incident.created_at
                                )
                            )}
                        </td>
                    </tr>
                `;
            })
            .join("");
}


async function loadIncidents() {
    const incidents = await fetchJson(
        `${API_BASE}/incidents`
    );

    renderIncidents(incidents);

    if (selectedIncidentId !== null) {
        const selectedExists = incidents.some(
            (incident) =>
                incident.id === selectedIncidentId
        );

        if (selectedExists) {
            await loadIncidentDetails(
                selectedIncidentId
            );
        }
    }
}


function renderIncidentDetails(
    incident,
    events
) {
    elements.incidentDetails.classList.remove(
        "empty-state"
    );

    const isOpen =
        incident.status === "open";

    const isAcknowledged =
        incident.status === "acknowledged";

    const isResolved =
        incident.status === "resolved";

    const eventsHtml = events.length
        ? events
              .map(
                  (event) => `
                    <div class="event">
                        <div class="event-type">
                            ${escapeHtml(
                                event.event_type
                            )}
                        </div>

                        <div class="event-description">
                            ${escapeHtml(
                                event.description
                            )}
                        </div>

                        <div class="event-time">
                            ${escapeHtml(
                                formatDateTime(
                                    event.created_at
                                )
                            )}
                        </div>
                    </div>
                `
              )
              .join("")
        : `
            <div class="empty-state">
                No event history available.
            </div>
        `;

    elements.incidentDetails.innerHTML = `
        <div class="detail-grid">
            <div class="detail-item">
                <div class="detail-label">
                    Incident ID
                </div>

                <div class="detail-value">
                    #${incident.id}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Status
                </div>

                <div class="detail-value">
                    ${createBadge(
                        incident.status
                    )}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Severity
                </div>

                <div class="detail-value">
                    ${createBadge(
                        incident.severity
                    )}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Source
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        incident.source
                    )}
                </div>
            </div>

            <div class="detail-item full-width">
                <div class="detail-label">
                    Title
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        incident.title
                    )}
                </div>
            </div>

            <div class="detail-item full-width">
                <div class="detail-label">
                    Description
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        incident.description
                    )}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Created
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        formatDateTime(
                            incident.created_at
                        )
                    )}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Updated
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        formatDateTime(
                            incident.updated_at
                        )
                    )}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Acknowledged
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        formatDateTime(
                            incident.acknowledged_at
                        )
                    )}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">
                    Resolved
                </div>

                <div class="detail-value">
                    ${escapeHtml(
                        formatDateTime(
                            incident.resolved_at
                        )
                    )}
                </div>
            </div>
        </div>

        <div class="incident-actions">
            <div class="incident-actions-header">
                <div>
                    <h4>Operator Actions</h4>

                    <p>
                        Manage the incident lifecycle from the dashboard.
                    </p>
                </div>
            </div>

            <div class="incident-action-buttons">
                <button
                    id="acknowledge-button"
                    class="button button-primary"
                    type="button"
                    ${!isOpen || isResolved ? "disabled" : ""}
                >
                    Acknowledge Incident
                </button>

                <button
                    id="resolve-button"
                    class="button button-primary"
                    type="button"
                    ${isResolved ? "disabled" : ""}
                >
                    Resolve Incident
                </button>
            </div>

            ${
                isResolved
                    ? `
                        <p class="action-status">
                            This incident has been resolved.
                        </p>
                    `
                    : isAcknowledged
                      ? `
                            <p class="action-status">
                                This incident has been acknowledged and is
                                awaiting resolution.
                            </p>
                        `
                      : `
                            <p class="action-status">
                                This incident is awaiting operator response.
                            </p>
                        `
            }
        </div>

        <div class="event-list">
            <h4>Incident History</h4>

            ${eventsHtml}
        </div>
    `;

    const acknowledgeButton =
        document.getElementById(
            "acknowledge-button"
        );

    const resolveButton =
        document.getElementById(
            "resolve-button"
        );

    if (acknowledgeButton) {
        acknowledgeButton.addEventListener(
            "click",
            () =>
                acknowledgeSelectedIncident(
                    incident.id
                )
        );
    }

    if (resolveButton) {
        resolveButton.addEventListener(
            "click",
            () =>
                resolveSelectedIncident(
                    incident.id
                )
        );
    }
}


async function loadIncidentDetails(
    incidentId
) {
    const [incident, events] =
        await Promise.all([
            fetchJson(
                `${API_BASE}/incidents/${incidentId}`
            ),
            fetchJson(
                `${API_BASE}/incidents/${incidentId}/events`
            ),
        ]);

    renderIncidentDetails(
        incident,
        events
    );
}


async function selectIncident(
    incidentId
) {
    selectedIncidentId = incidentId;

    try {
        const incidents = await fetchJson(
            `${API_BASE}/incidents`
        );

        renderIncidents(incidents);

        elements.incidentDetails.innerHTML = `
            <div class="empty-state">
                Loading incident details...
            </div>
        `;

        await loadIncidentDetails(
            incidentId
        );
    } catch (error) {
        console.error(error);

        elements.incidentDetails.innerHTML = `
            <div class="empty-state">
                Unable to load incident details.
            </div>
        `;

        showError(error.message);
    }
}


async function createIncident(event) {
    event.preventDefault();

    clearError();

    const title =
        document.getElementById(
            "incident-title"
        ).value.trim();

    const description =
        document.getElementById(
            "incident-description"
        ).value.trim();

    const severity =
        document.getElementById(
            "incident-severity"
        ).value;

    const source =
        document.getElementById(
            "incident-source"
        ).value.trim();

    if (!title || !description || !severity || !source) {
        setCreateIncidentStatus(
            "Please complete all required fields."
        );

        return;
    }

    const button =
        elements.createIncidentButton;

    if (button) {
        button.disabled = true;
        button.textContent =
            "Creating...";
    }

    setCreateIncidentStatus(
        "Creating incident..."
    );

    try {
        const incident = await fetchJson(
            `${API_BASE}/incidents`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    title,
                    description,
                    severity,
                    source,
                }),
            }
        );

        selectedIncidentId = incident.id;

        elements.createIncidentForm.reset();

        setCreateIncidentStatus(
            `Incident #${incident.id} created successfully.`
        );

        await refreshDashboard();
    } catch (error) {
        console.error(error);

        setCreateIncidentStatus(
            "Unable to create incident."
        );

        showError(error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent =
                "Create Incident";
        }
    }
}


async function acknowledgeSelectedIncident(
    incidentId
) {
    clearError();

    const button =
        document.getElementById(
            "acknowledge-button"
        );

    if (button) {
        button.disabled = true;
        button.textContent =
            "Acknowledging...";
    }

    try {
        await fetchJson(
            `${API_BASE}/incidents/${incidentId}/acknowledge`,
            {
                method: "POST",
            }
        );

        selectedIncidentId = incidentId;

        await refreshDashboard();
    } catch (error) {
        console.error(error);
        showError(error.message);

        if (button) {
            button.disabled = false;
            button.textContent =
                "Acknowledge Incident";
        }
    }
}


async function resolveSelectedIncident(
    incidentId
) {
    clearError();

    const button =
        document.getElementById(
            "resolve-button"
        );

    if (button) {
        button.disabled = true;
        button.textContent =
            "Resolving...";
    }

    try {
        await fetchJson(
            `${API_BASE}/incidents/${incidentId}/resolve`,
            {
                method: "POST",
            }
        );

        selectedIncidentId = incidentId;

        await refreshDashboard();
    } catch (error) {
        console.error(error);
        showError(error.message);

        if (button) {
            button.disabled = false;
            button.textContent =
                "Resolve Incident";
        }
    }
}


async function refreshDashboard() {
    clearError();

    elements.refreshButton.disabled = true;
    elements.refreshButton.textContent =
        "Refreshing...";

    try {
        await loadSystemHealth();
        await loadStatistics();
        await loadIncidents();

        elements.lastUpdated.textContent =
            new Date().toLocaleTimeString();
    } catch (error) {
        console.error(error);

        setSystemUnhealthy(
            "Unable to communicate with the incident platform API."
        );

        showError(error.message);
    } finally {
        elements.refreshButton.disabled = false;
        elements.refreshButton.textContent =
            "Refresh";
    }
}


if (elements.createIncidentForm) {
    elements.createIncidentForm.addEventListener(
        "submit",
        createIncident
    );
}


elements.refreshButton.addEventListener(
    "click",
    refreshDashboard
);


elements.incidentsTableBody.addEventListener(
    "click",
    async (event) => {
        const row =
            event.target.closest(
                "tr[data-incident-id]"
            );

        if (!row) {
            return;
        }

        const incidentId = Number(
            row.dataset.incidentId
        );

        if (!Number.isInteger(incidentId)) {
            return;
        }

        await selectIncident(
            incidentId
        );
    }
);


refreshDashboard();


setInterval(
    refreshDashboard,
    30_000
);
