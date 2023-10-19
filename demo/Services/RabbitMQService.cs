using RabbitMQ.Client;
using System;
using System.Text;
using System.Text.Json;
using demo.Data;
public class RabbitMqService
{
    private readonly IConnection _connection;
    private readonly IModel _channel;
    public uint InitialQueueLength 
    {
        get
        {
            // Get the message count for the queue
            var queueInfo = _channel.QueueDeclarePassive(standard_queueName);
            return queueInfo.MessageCount;
        }
    }

    private const string irq_exchange = "irq_exchange";
    private const string irq_routingKey = "irq_key";

    private const string  standard_exchange = "standard_exchange";
    private const string  standard_routingKey = "standard_key";
    private const string  standard_queueName = "standard"; 
    
    public RabbitMqService()
    {
        var factory = new ConnectionFactory
        {
            HostName = "rabbitmq",
            Port = 5672,             // RabbitMQ default port
        };

        _connection = factory.CreateConnection();
        _channel = _connection.CreateModel();
        _channel.BasicQos(0, 1, false);

        _channel.ExchangeDeclare(exchange: irq_exchange, type: ExchangeType.Direct);

        _channel.ExchangeDeclare(exchange: standard_exchange, type: ExchangeType.Direct);
        _channel.QueueDeclare(queue: standard_queueName,
                                durable: false,
                                exclusive: false,
                                autoDelete: false,
                                arguments: null);

    }

    public void SendInterrupt()
    {
        var messageBody = Encoding.UTF8.GetBytes("{}");

        _channel.BasicPublish(exchange: irq_exchange,
                              routingKey: irq_routingKey,
                              basicProperties: null,
                              body: messageBody);
    }

    public void SendMusicGenRequest(string text, string duration, string audio_file)
    {
        var request = new MusicGenRequest
        {
            Text = text,
            Duration = duration,
            AudioFile = audio_file
        };

        var jsonMessage = JsonSerializer.Serialize(request);
        var messageBody = Encoding.UTF8.GetBytes(jsonMessage);

        _channel.BasicPublish(exchange: standard_exchange,
                              routingKey: standard_routingKey,
                              basicProperties: null,
                              body: messageBody);
    }
}
