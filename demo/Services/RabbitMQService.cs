using RabbitMQ.Client;
using System;
using System.Text;
using System.Text.Json;
using demo.Data;
public class RabbitMqService
{
    private readonly IConnection _connection;
    private readonly IModel _channel;

    public RabbitMqService()
    {
        var factory = new ConnectionFactory
        {
            HostName = "rabbitmq",
            Port = 5672,             // RabbitMQ default port
        };

        _connection = factory.CreateConnection();
        _channel = _connection.CreateModel();
    }

    public void SendInterrupt()
    {
        var exchangeName = "irq_exchange";
        var routingKey = "irq_key";

        _channel.ExchangeDeclare(exchange: exchangeName, type: ExchangeType.Direct);

        var messageBody = Encoding.UTF8.GetBytes("{}");

        _channel.BasicPublish(exchange: exchangeName,
                              routingKey: routingKey,
                              basicProperties: null,
                              body: messageBody);
    }

    public void SendMusicGenRequest(string text, string duration, string audio_file)
    {
        var exchangeName = "standard_exchange";
        var routingKey = "standard_key";

        _channel.ExchangeDeclare(exchange: exchangeName, type: ExchangeType.Direct);

        var request = new MusicGenRequest
        {
            Text = text,
            Duration = duration,
            AudioFile = audio_file
        };

        var jsonMessage = JsonSerializer.Serialize(request);
        var messageBody = Encoding.UTF8.GetBytes(jsonMessage);

        _channel.BasicPublish(exchange: exchangeName,
                              routingKey: routingKey,
                              basicProperties: null,
                              body: messageBody);
    }
}
