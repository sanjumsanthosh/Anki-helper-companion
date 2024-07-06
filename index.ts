import { readdir, access } from "node:fs/promises";

Bun.serve({
    port: 3939, 
    async fetch(req) {
        const url = new URL(req.url);
        // Create a base response headers object
        const headers = new Headers({
            "Content-Type": "text/json",
            "Access-Control-Allow-Origin": "*", 
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "X-Requested-With, Content-Type, Accept, Origin, Authorization"
        });


        if (req.method === "OPTIONS") {
            return new Response(null, { headers, status: 204 });
        }

        if (url.pathname === "/") return new Response("Home page!", { headers });
        if (url.pathname === "/blog") return new Response("Blog!", { headers });
        if (url.pathname === "/health-check") return new Response("{ status: 'ok' }", { headers , status: 200 });

        // /list
        if (url.pathname === "/list") {
            // get all files in path "static" and return them as a list
            let files = await readdir("static");

            // just dot files .dot
            files = files.filter((file) => file.endsWith(".dot"));

            // remove the .dot extension
            files = files.map((file) => file.replace(".dot", ""));
            return new Response(JSON.stringify(files), { headers });
        }

        // /{filename}/dot
        if (url.pathname.endsWith("/dot")) {
            const filename = url.pathname.replace("/dot", "");
            let file = null;

            // check file exist
            if (await fileExists(`static${filename}.dot`)) {
                console.log(`trying to get file: static${filename}.dot`)
                file = Bun.file(`static${filename}.dot`);
                return new Response(file, { headers });
            } else {
                return new Response("404!", { headers, status: 404 });
            }
        }

        

        // /{filename}/json
        if (url.pathname.endsWith("/json") && req.method === "GET") {
            const filename = url.pathname.replace("/json", "");
            let file = null;
            if (await fileExists(`static${filename}.json`)) {
                console.log(`trying to get file: static${filename}.json`)
                file = Bun.file(`static${filename}.json`);
                return new Response(file, { headers });
            } else {
                return new Response("404!", { headers, status: 404 });
            }
        }

        // /{filename}/json -> post with file to save the file
        if (url.pathname.endsWith("/json") && req.method === "POST") {
            const filename = url.pathname.replace("/json", "");
            let file = await req.json();
            console.log(`trying to save file: static${filename}.json`)
            await Bun.write(`static${filename}.json`, JSON.stringify(file));
            return new Response(JSON.stringify({"status": "File saved!"}), { headers });
        }

        return new Response("404!", { headers, status: 404 });
    },
});

// check if file exists
async function fileExists(path: string) {
    try {
        await access(path);
        console.log(`file ${path} exists`)
        return true;
    }
    catch (err) {
        console.log(`file ${path} does not exists`, err)
        return false;
    }
}

console.log("Server started on port http://localhost:3939");