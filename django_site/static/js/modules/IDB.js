
//checking if the browser has compatibility to use indexed database
if (!indexedDB in window)
    {
        console.error("This browser does not support the use of indexed databases (iDB).")
        window.alert("This browser does not support the use of indexed databases (iDB).")
    }

//open database specified with identifier DB_NAME
const idbPromise = indexedDB.open(DB_NAME)

//on successful open
idbPromise.onsuccess = (e)=>{
    DB = e.target.result
    console.log(`We successfully opened database ${DB_NAME}`)
    if (!window.sessionStorage.getItem("placeholder"))
    {
       DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).clear().onsuccess = ()=>{
           window.sessionStorage.setItem("placeholder", "")
       }
    }
    //event which trigger when the page/browser is closed or some error with database/transactions happens during runtime
    DB.onclose = ()=>{
    const dbTransaction = DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).clear()
    dbTransaction.onsuccess = ()=>{
        dbTransaction.transaction.commit()
        DB.close()
    }
}
}

//on error open
idbPromise.onerror=(ev)=>{
    console.error(`Could not open a database named ${DB_NAME}. Database error: ${ev.target.errorCode}`)
    console.dir(ev)
}

//when the database needs to be updated to newer version
idbPromise.onupgradeneeded=(e)=>{
 DB =  e.target.result
 console.log(`Upgrading to version ${DB.version}`);
 const objectStore = DB.createObjectStore(STORE_NAME, {autoIncrement:true})
    objectStore.createIndex("ID", "userId", {unique:true})
    objectStore.createIndex("platform", "platform", {unique:false})
    objectStore.transaction.oncomplete =()=>{
            console.log(`Object store ${STORE_NAME} created successfully.`)
 }
}
