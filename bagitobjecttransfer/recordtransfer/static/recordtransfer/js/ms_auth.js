async function getToken() {

    let accessToken = "";
    // Scopes for access to any files in OneDrive created or shared with the user
    // and in any Team the user is part of.
    authParams = { scopes: ["Files.Read.All", "Sites.Read.All"] };

    try {

        // see if we have already the idtoken saved
        const resp = await app.acquireTokenSilent(authParams);
        accessToken = resp.accessToken;

    } catch (e) {

        // per examples we fall back to popup
        const resp = await app.loginPopup(authParams);
        app.setActiveAccount(resp.account);

        if (resp.idToken) {

            const resp2 = await app.acquireTokenSilent(authParams);
            accessToken = resp2.accessToken;

        }
    }

    return accessToken;
}
