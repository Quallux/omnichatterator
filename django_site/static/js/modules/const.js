/**
 * Database name.
 * @type {string}
 */
const DB_NAME = "Omnichatterator"
/**
 * Store name.
 * @type {string}
 */
const STORE_NAME = "ConvoHistory"
/**
 * Name of platforms.
 *
 * @type {string[]}
 */
const PLATFORMS = ["twitter", "messenger", "gmail"]
/**
 *Reference to the open database. Default value is null.
 *
 * @type {null|IDBDatabase}
 */
let DB = null
/**
 * List of timestamps.
 *
 * @type {string[]}
 */
let TIME_STAMP = ["0","0","0"]

/**
 * Maximal length of message or subject for displaying in contact list.
 *
 * @type {number}
 */
const MESSAGE_CONTACT_MAX_LENGTH = 26