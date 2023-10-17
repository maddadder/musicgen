using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using demo.Data;
using demo.Hubs;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);
builder.Logging.AddConfiguration(builder.Configuration.GetSection("Logging"));

// Add services to the container.
builder.Services.AddRazorPages();
builder.Services.AddServerSideBlazor();
builder.Services.AddSignalR();

builder.Logging.SetMinimumLevel(LogLevel.Information);
builder.Services.AddSingleton<WeatherForecastService>();
builder.Services.AddSingleton<RabbitMqService>();
builder.Services.AddSingleton<FileUploadService>();
builder.Services.AddSingleton<IRabbitMQPersistentConnection, DefaultRabbitMQPersistentConnection>();
builder.Services.AddHostedService<EventBusRabbitMQ>();

var app = builder.Build();
app.Logger.LogInformation("Host built successfully.");
// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(
        Path.Combine(Directory.GetCurrentDirectory(), "audio")),
    RequestPath = "/audio" // Specify the request path for the "audio" folder
});

app.UseRouting();

app.MapBlazorHub();
app.MapFallbackToPage("/_Host");
app.MapHub<ChatHub>(ChatHub.HubUrl);
app.Run();
