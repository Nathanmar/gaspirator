using Microsoft.AspNetCore.Mvc;
using Dapper;
using Npgsql;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.SignalR;
using Serilog;

// Load KEY=VALUE pairs from a local .env so scaffold-time settings (PORT,
// CORS_ORIGIN) apply to `dotnet run`. Real environment variables win.
if (File.Exists(".env"))
{
    foreach (var rawLine in File.ReadAllLines(".env"))
    {
        var line = rawLine.Trim();
        if (line.Length == 0 || line.StartsWith('#')) continue;
        var separatorIndex = line.IndexOf('=');
        if (separatorIndex <= 0) continue;
        var key = line[..separatorIndex].Trim();
        var value = line[(separatorIndex + 1)..].Trim();
        if (value.Length > 0 && Environment.GetEnvironmentVariable(key) is null)
        {
            Environment.SetEnvironmentVariable(key, value);
        }
    }
}

var builder = WebApplication.CreateBuilder(args);

// Honor a PORT env var (binding all interfaces so containers/PaaS work);
// an explicit ASPNETCORE_URLS always wins.
var port = builder.Configuration["PORT"];
if (!string.IsNullOrEmpty(port) && string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ASPNETCORE_URLS")))
{
    builder.WebHost.UseUrls($"http://+:{port}");
}

builder.Services.AddControllers();
builder.Host.UseSerilog((context, configuration) =>
    configuration.ReadFrom.Configuration(context.Configuration).WriteTo.Console());

builder.Services.AddAuthentication();
builder.Services.AddAuthorization();
builder.Services.AddSignalR();
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379";
});
builder.Services.AddHostedService<Worker>();
// CORS: pinned to the CORS_ORIGIN env var when set, permissive otherwise.
var corsOrigin = builder.Configuration["CORS_ORIGIN"];
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        if (string.IsNullOrEmpty(corsOrigin))
        {
            policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod();
        }
        else
        {
            policy.WithOrigins(corsOrigin).AllowAnyHeader().AllowAnyMethod();
        }
    });
});

var app = builder.Build();

app.UseCors();

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/", () => Results.Ok(new
{
    name = "my-app",
    framework = "aspnet-mvc",
    status = "ok"
}));

app.MapControllers();
app.MapHub<UpdatesHub>("/hubs/updates");

app.Run();

public partial class Program;

public sealed class TodoItem
{
    public int Id { get; set; }
    public required string Title { get; set; }
    public bool Complete { get; set; }
}

public sealed record TodoInput(string Title);

[ApiController]
[Route("api/[controller]")]
public sealed class TodosController : ControllerBase
{
    private readonly IConfiguration configuration;

    public TodosController(IConfiguration configuration)
    {
        this.configuration = configuration;
    }

    [HttpGet]
    public async Task<IActionResult> GetTodos()
    {
        await using var db = TodoDapper.CreateConnection(TodoDapper.GetConnectionString(configuration));
        await TodoDapper.EnsureSchemaAsync(db);
        var todos = await db.QueryAsync<TodoItem>("SELECT Id, Title, Complete FROM Todos ORDER BY Id");
        return Ok(todos);
    }

    [HttpPost]
    public async Task<IActionResult> CreateTodo(TodoInput input)
    {
        await using var db = TodoDapper.CreateConnection(TodoDapper.GetConnectionString(configuration));
        await TodoDapper.EnsureSchemaAsync(db);
        const string sql = """
            INSERT INTO Todos (Title, Complete)
            VALUES (@Title, @Complete)
            RETURNING Id, Title, Complete
            """;
        var todo = await db.QuerySingleAsync<TodoItem>(sql, new { input.Title, Complete = false });
        return Created($"/api/todos/{todo.Id}", todo);
    }
}

public static class TodoDapper
{
    public static async Task EnsureSchemaAsync(System.Data.Common.DbConnection db)
    {
        const string sql = """
            CREATE TABLE IF NOT EXISTS Todos (
                Id SERIAL PRIMARY KEY,
                Title TEXT NOT NULL,
                Complete BOOLEAN NOT NULL DEFAULT FALSE
            )
            """;
        await db.ExecuteAsync(sql);
    }

    public static string GetConnectionString(IConfiguration configuration)
    {
        return configuration.GetConnectionString("DefaultConnection")
            ?? "Host=localhost;Port=5432;Database=my-app;Username=postgres;Password=postgres";
    }

    public static System.Data.Common.DbConnection CreateConnection(string connectionString)
    {
        return new NpgsqlConnection(connectionString);
    }
}
public sealed class UpdatesHub : Hub
{
    public Task Broadcast(string message) => Clients.All.SendAsync("update", message);
}
public sealed class Worker(ILogger<Worker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            logger.LogInformation("Worker heartbeat at {Time}", DateTimeOffset.UtcNow);
            await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
        }
    }
}
