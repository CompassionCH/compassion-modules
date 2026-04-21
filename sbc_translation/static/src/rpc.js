/** @odoo-module */

/**
 * Minimal JSON-RPC helper for portal/frontend context.
 * Authenticates via the Odoo session cookie (no JWT needed).
 * Mirrors the interface of the Odoo `orm` service so DAO files stay readable.
 */

let _idCounter = 1;

/**
 * Low-level call to Odoo's /web/dataset/call_kw endpoint.
 * @param {string} model
 * @param {string} method
 * @param {Array}  args    - positional arguments
 * @param {Object} kwargs  - keyword arguments
 * @returns {Promise<*>}
 */
async function callKw(model, method, args, kwargs = {}) {
    const response = await fetch("/web/dataset/call_kw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            id: _idCounter++,
            params: {
                model,
                method,
                args,
                kwargs: { context: {}, ...kwargs },
            },
        }),
    });
    const json = await response.json();
    if (json.error) {
        const msg =
            json.error.data?.message ||
            json.error.message ||
            "JSON-RPC error";
        throw new Error(msg);
    }
    return json.result;
}

/**
 * Search for records matching a domain.
 * @param {string} model
 * @param {Array}  domain
 * @param {Object} options - { offset, limit, order }
 * @returns {Promise<number[]>}
 */
export async function search(model, domain, options = {}) {
    return callKw(model, "search", [domain], options);
}

/**
 * Count records matching a domain.
 * @param {string} model
 * @param {Array}  domain
 * @returns {Promise<number>}
 */
export async function searchCount(model, domain) {
    return callKw(model, "search_count", [domain]);
}

/**
 * Search + read records.
 * @param {string}   model
 * @param {Array}    domain
 * @param {string[]} fields
 * @param {Object}   options - { offset, limit, order }
 * @returns {Promise<Object[]>}
 */
export async function searchRead(model, domain, fields, options = {}) {
    return callKw(model, "search_read", [domain], { fields, ...options });
}

/**
 * Call a method on a model.
 * @param {string} model
 * @param {string} method
 * @param {Array}  args   - positional args (first element is usually a list of IDs for record methods)
 * @param {Object} kwargs
 * @returns {Promise<*>}
 */
export async function call(model, method, args, kwargs = {}) {
    return callKw(model, method, args, kwargs);
}

const rpc = { search, searchCount, searchRead, call };
export default rpc;
