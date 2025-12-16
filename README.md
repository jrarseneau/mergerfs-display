# 🗄️ MergerFS Pool Monitor

A sophisticated web application and command-line tool for monitoring MergerFS pools and their underlying storage devices. Built with Python, it provides real-time insights into your storage infrastructure with beautiful visualizations.

## ✨ Features

- 📊 **Multi-Pool Support**: Monitor multiple MergerFS pools simultaneously
- 🖥️ **Dual Interface**: Both CLI and web-based interfaces
- 🌡️ **Temperature Monitoring**: Track disk temperatures using smartctl
- 💾 **Space Analytics**: Detailed space usage statistics for each branch
- 🎨 **Beautiful UI**: Unraid-inspired web interface with gradient designs
- 🔍 **Auto-Detection**: Automatically discovers MergerFS branches and physical disks
- ⚡ **Self-Contained**: Minimal dependencies, easy to deploy

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- MergerFS filesystem
- smartmontools (for temperature monitoring)
- xattr support

### Python Dependencies
All Python dependencies are listed in `requirements.txt`:
- flask
- pyyaml
- psutil
- rich
- click
- pyxattr

## 🚀 Installation

### 1. Clone or Download

```bash
cd /path/to/mergerfs-display
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install System Dependencies

**Debian/Ubuntu:**
```bash
sudo apt-get install smartmontools attr
```

**RHEL/CentOS/Fedora:**
```bash
sudo yum install smartmontools attr
```

**Arch Linux:**
```bash
sudo pacman -S smartmontools attr
```

### 4. Create Configuration

Copy the example configuration and customize it:

```bash
cp config.example.yaml config.yaml
nano config.yaml
```

## ⚙️ Configuration

Edit `config.yaml` to define your MergerFS pools:

```yaml
# MergerFS Pool Monitor Configuration

pools:
  - name: "Main Storage Pool"
    path: "/mnt/pool"

  - name: "Media Pool"
    path: "/mnt/media"

# Web server configuration (optional)
web:
  port: 8090  # Port for the web interface
  host: "0.0.0.0"  # Host to bind to (0.0.0.0 allows external access)
```

### Configuration Options

#### Pools Section
- `name`: Human-readable name for the pool (optional)
- `path`: Path to the MergerFS mount point (required)

#### Web Section
- `port`: Port number for the web server (default: 8090)
- `host`: Host address to bind to (default: 0.0.0.0)

## 📖 Usage

### Command-Line Interface

Display pool information in the terminal:

```bash
./mergerfs-monitor.py
```

Or explicitly use the CLI command:

```bash
./mergerfs-monitor.py cli
```

Use a custom config file:

```bash
./mergerfs-monitor.py --config /path/to/config.yaml
```

### Web Interface

Start the web server:

```bash
./mergerfs-monitor.py web
```

With custom port and host:

```bash
./mergerfs-monitor.py web --port 9000 --host 127.0.0.1
```

Then open your browser to: `http://localhost:8090` (or your configured port)

### CLI Options

```bash
./mergerfs-monitor.py --help
```

**Available commands:**
- `cli`: Display pool information in terminal (default)
- `web`: Start the web interface

**Global options:**
- `--config, -c`: Path to configuration file
- `--help`: Show help message

**Web command options:**
- `--port, -p`: Override web server port
- `--host, -h`: Override web server host

## 📊 What You'll See

### CLI Output

The CLI displays a beautiful table for each pool showing:

1. **Branch**: Full path to the MergerFS branch
2. **Physical Disk**: The underlying physical disk device (e.g., /dev/sda)
3. **Temperature**: Current disk temperature in Celsius (or N/A)
4. **Total Space**: Total capacity of the disk
5. **Used Space**: Amount of space used
6. **Free Space**: Amount of space available
7. **Free %**: Percentage of free space (color-coded)

Plus a summary section with:
- Total number of branches
- Aggregate space statistics
- Overall free space percentage

### Web Interface

The web interface provides:

- 🎨 Modern, responsive design inspired by Unraid
- 📈 Visual progress bars for space usage
- 🌡️ Color-coded temperature indicators:
  - 🟢 Green: < 45°C (optimal)
  - 🟡 Yellow: 45-55°C (warm)
  - 🔴 Red: > 55°C (hot)
- 📊 Summary cards for quick overview
- 🔄 Manual refresh button
- 📱 Mobile-friendly responsive layout

## 🔧 How It Works

### Branch Detection

The tool uses the MergerFS extended attributes to discover branches:

```bash
xattr -l /mnt/pool/.mergerfs
```

It reads the `user.mergerfs.branches` attribute which contains all branch paths.

### Physical Disk Detection

For each branch, the tool:
1. Uses `df` to find the mounted device
2. Resolves device mappers and LVM volumes
3. Strips partition numbers to get the base disk device

### Temperature Reading

Temperature is retrieved using:
1. **Primary**: `smartctl` for SMART-enabled drives
2. **Fallback**: sysfs hwmon sensors

### Space Calculation

Space statistics use `psutil.disk_usage()` which works correctly with:
- Regular filesystems (ext4, xfs, etc.)
- ZFS pools
- Btrfs filesystems
- LVM volumes

## 🐛 Troubleshooting

### "Configuration file not found"

Make sure you've created `config.yaml` from `config.example.yaml`:

```bash
cp config.example.yaml config.yaml
```

### "Path does not appear to be a MergerFS mount"

Ensure:
1. The path is actually a MergerFS mount point
2. You have read permissions
3. The `.mergerfs` control file exists

### Temperature shows "N/A"

This can happen if:
1. smartmontools is not installed
2. The disk doesn't support SMART
3. You don't have permission to access SMART data

Run with sudo to test:
```bash
sudo ./mergerfs-monitor.py
```

### Permission Denied Errors

You may need elevated permissions to:
- Read SMART data
- Access certain disk information

Run with sudo if needed:
```bash
sudo ./mergerfs-monitor.py web
```

## 🛠️ Development

### Project Structure

```
mergerfs-display/
├── mergerfs_monitor/          # Main package
│   ├── __init__.py           # Package initializer
│   ├── config.py             # Configuration parser
│   ├── mergerfs.py           # MergerFS branch detection
│   ├── disk_info.py          # Disk information collector
│   ├── cli.py                # CLI interface
│   └── web.py                # Web interface
├── mergerfs-monitor.py        # Main entry point
├── requirements.txt           # Python dependencies
├── config.example.yaml        # Example configuration
└── README.md                  # This file
```

### Adding Features

The modular design makes it easy to extend:

- **New data sources**: Add to `disk_info.py`
- **CLI enhancements**: Modify `cli.py`
- **Web UI changes**: Update templates in `web.py`
- **Configuration options**: Extend `config.py`

## 📝 API Endpoint

The web interface also provides a JSON API:

```bash
curl http://localhost:8090/api/pools
```

This returns detailed information about all pools in JSON format, useful for:
- Monitoring integrations
- Custom dashboards
- Automation scripts

## 🔒 Security Considerations

- The web interface has no authentication by default
- Consider using a reverse proxy (nginx, Caddy) with authentication if exposing externally
- The tool requires elevated permissions for full functionality
- Run behind a firewall for production use

## 🚦 Future Enhancements

Potential features for future versions:

- [ ] Auto-refresh for web interface
- [ ] Historical data tracking
- [ ] Email/webhook alerts for low space or high temperatures
- [ ] ZFS/Btrfs native support with pool detection
- [ ] Docker container deployment
- [ ] Prometheus metrics export
- [ ] Dark mode toggle for web UI

## 📄 License

This project is provided as-is for personal and commercial use.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## 👏 Acknowledgments

- Inspired by Unraid's disk management interface
- Built with Flask, Rich, and other excellent Python libraries
- Thanks to the MergerFS project for the amazing filesystem

---

**Made with ❤️ for storage enthusiasts**