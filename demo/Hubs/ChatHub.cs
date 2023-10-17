using Microsoft.AspNetCore.SignalR;

namespace demo.Hubs;

public class ChatHub : Hub
{
    public const string HubUrl = "/chat";

    public async Task Broadcast(string message)
    {
        await Clients.All.SendAsync("Broadcast", message);
    }
    public override async Task OnConnectedAsync()
    {
        await base.OnConnectedAsync();
        // Add logging or send a message upon connection
        //await Clients.All.SendAsync("Broadcast", "A new client has connected.");
    }

    public override async Task OnDisconnectedAsync(Exception exception)
    {
        // Add logging or send a message upon disconnection
        await Clients.All.SendAsync("Broadcast", "A client has disconnected.");
        await base.OnDisconnectedAsync(exception);
    }
}