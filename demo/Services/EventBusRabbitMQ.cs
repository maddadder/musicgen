
using System.Text;
using System.Text.Json;
using demo.Data;
using demo.Hubs;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.SignalR.Client;
using Microsoft.Extensions.DependencyInjection;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

public class EventBusRabbitMQ : IDisposable, IHostedService
{
    private HubConnection _hubConnection;
    private readonly IRabbitMQPersistentConnection _persistentConnection;
    private readonly ILogger<EventBusRabbitMQ> _logger;
    private IModel _consumerChannel;
    private string _queueName;

    public EventBusRabbitMQ(ILogger<EventBusRabbitMQ> logger, IRabbitMQPersistentConnection persistentConnection)
    {
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        _persistentConnection = persistentConnection ?? throw new ArgumentNullException(nameof(persistentConnection));
        
    }



    public void Dispose()
    {
        if (_consumerChannel != null)
        {
            _consumerChannel.Dispose();
        }

    }

    private void StartBasicConsume()
    {
        _logger.LogInformation("Starting RabbitMQ basic consume");

        if (_consumerChannel != null)
        {
            var consumer = new AsyncEventingBasicConsumer(_consumerChannel);

            
            
            consumer.Received += Consumer_Received;

            _consumerChannel.BasicConsume(
                queue: _queueName,
                autoAck: false,
                consumer: consumer);
        }
        else
        {
            _logger.LogInformation("StartBasicConsume can't call on _consumerChannel == null");
        }
    }

    private async Task Consumer_Received(object sender, BasicDeliverEventArgs eventArgs)
    {
        var eventName = eventArgs.RoutingKey;
        var message = Encoding.UTF8.GetString(eventArgs.Body.Span);

        try
        {
            if (message.ToLowerInvariant().Contains("throw-fake-exception"))
            {
                throw new InvalidOperationException($"Fake exception requested: \"{message}\"");
            }

            await ProcessEvent(eventName, message);
        }
        catch (Exception ex)
        {
            _logger.LogInformation($"Error Processing message {ex.ToString()}" );
        }

        // Even on exception we take the message off the queue.
        // in a REAL WORLD app this should be handled with a Dead Letter Exchange (DLX). 
        // For more information see: https://www.rabbitmq.com/dlx.html
        _consumerChannel.BasicAck(eventArgs.DeliveryTag, multiple: false);
    }

    private IModel CreateConsumerChannel()
    {
        if (!_persistentConnection.IsConnected)
        {
            _persistentConnection.TryConnect();
        }

        _logger.LogInformation("Creating RabbitMQ consumer channel");

        var channel = _persistentConnection.CreateModel();

        channel.ExchangeDeclare(exchange: "ack_exchange",
                                type: "direct");

        channel.QueueDeclare(queue: _queueName,
                                durable: false,
                                exclusive: false,
                                autoDelete: false,
                                arguments: null);

        channel.CallbackException += (sender, ea) =>
        {
            _logger.LogInformation("Recreating RabbitMQ consumer channel");

            _consumerChannel.Dispose();
            _consumerChannel = CreateConsumerChannel();
            StartBasicConsume();
        };
        
        return channel;
    }

    private async Task ProcessEvent(string eventName, string message)
    {
        // Create the chat client
        string baseUrl = "http://localhost:8080/";

        string _hubUrl = baseUrl.TrimEnd('/') + ChatHub.HubUrl;

        _hubConnection = new HubConnectionBuilder()
            .WithUrl(_hubUrl)
            .Build();
        _logger.LogInformation("starting _hubConnection");
        
        await _hubConnection.StartAsync();
        
        var messageObject = JsonSerializer.Deserialize<MusicGenResponse>(message);

        if (messageObject != null && !string.IsNullOrEmpty(messageObject.audio_data))
        {
            
            string guid = $"{Guid.NewGuid()}";

            _logger.LogInformation("Save the audio data to disk");
            var decodedContent = Convert.FromBase64String(messageObject.audio_data);
            var mp3SavePath = $"audio/{guid}.mp3";
            File.WriteAllBytes(mp3SavePath, decodedContent);

            if(!string.IsNullOrEmpty(messageObject.Text))
            {
                _logger.LogInformation("Save the audio text to disk");
                var txtSavePath = $"audio/{guid}.txt";
                File.WriteAllText(txtSavePath, messageObject.Text);
            }
            await _hubConnection.SendAsync("Broadcast", "success");
            
        }
        else if (messageObject != null)
        {
            _logger.LogInformation("Could not save the audio data to disk");
            await _hubConnection.SendAsync("Broadcast", messageObject.Result);
        }
        else
        {
            _logger.LogInformation("Could not save the audio data to disk");
            await _hubConnection.SendAsync("Broadcast", "failed to process message");
        }

    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        
        _queueName = "acknowledgment_queue";
        _consumerChannel = CreateConsumerChannel();
        StartBasicConsume();
    }

    public async Task StopAsync(CancellationToken cancellationToken)
    {
        this.Dispose();
    }
}
