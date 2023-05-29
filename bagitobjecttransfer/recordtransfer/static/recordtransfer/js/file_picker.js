const baseUrl = "https://onedrive.live.com/picker";

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

const channelId = uuidv4();

// the options we pass to the picker page through the querystring
const params = {
    sdk: "8.0",
    entry: {
        oneDrive: {
            files: {},
        }
    },
    authentication: {},
    messaging: {
        origin: "http://localhost:3000",
        channelId: channelId,
    },
    typesAndSources: {
        mode: "files",
        pivots: {
            oneDrive: true,
            recent: true,
        },
    },
};

let win = null;
let port = null;

async function launchPicker(e) {

    e.preventDefault();

    win = window.open("", "Picker", "width=800,height=600")

    if (preToken == "") {
        const authToken = await getToken();
    } else {
        const authToken = preToken;
    }

    const queryString = new URLSearchParams({
        filePicker: JSON.stringify(params),
    });

    const url = `${baseUrl}?${queryString}`;

    const form = win.document.createElement("form");
    form.setAttribute("action", url);
    form.setAttribute("method", "POST");
    win.document.body.append(form);

    const input = win.document.createElement("input");
    input.setAttribute("type", "hidden")
    input.setAttribute("name", "access_token");
    input.setAttribute("value", authToken);
    form.appendChild(input);

    form.submit();

    window.addEventListener("message", (event) => {

        if (event.source && event.source === win) {

            const message = event.data;

            if (message.type === "initialize" && message.channelId === params.messaging.channelId) {

                port = event.ports[0];

                port.addEventListener("message", messageListener);

                port.start();

                port.postMessage({
                    type: "activate",
                });
            }
        }
    });
}

async function messageListener(message) {
    switch (message.data.type) {

        case "notification":
            console.log(`notification: ${message.data}`);
            break;

        case "command":

            port.postMessage({
                type: "acknowledge",
                id: message.data.id,
            });

            const command = message.data.data;

            switch (command.command) {

                case "authenticate":

                    // getToken is from scripts/auth.js
                    const token = await getToken();

                    if (typeof token !== "undefined" && token !== null) {

                        port.postMessage({
                            type: "result",
                            id: message.data.id,
                            data: {
                                result: "token",
                                token,
                            }
                        });

                    } else {
                        console.error(`Could not get auth token for command: ${JSON.stringify(command)}`);
                    }

                    break;

                case "close":

                    win.close();
                    break;

                case "pick":

                    console.log(`Picked: ${JSON.stringify(command)}`);

                    document.getElementById("pickedFiles").innerHTML = `<pre>${JSON.stringify(command, null, 2)}</pre>`;

                    port.postMessage({
                        type: "result",
                        id: message.data.id,
                        data: {
                            result: "success",
                        },
                    });

                    win.close();

                    break;

                default:

                    console.warn(`Unsupported command: ${JSON.stringify(command)}`, 2);

                    port.postMessage({
                        result: "error",
                        error: {
                            code: "unsupportedCommand",
                            message: command.command
                        },
                        isExpected: true,
                    });
                    break;
            }

            break;
    }
}

$(() => {
    $(document).ready(function() {
        $("#oneDrivePicker_launch").on("click", function(evt) {
            launchPicker(evt);
        });
        window.addEventListener("message", messageListener);
    });
});
