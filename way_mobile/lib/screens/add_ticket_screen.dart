import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class AddTicketScreen extends StatefulWidget {
  const AddTicketScreen({super.key});

  @override
  State<AddTicketScreen> createState() => _AddTicketScreenState();
}

class _AddTicketScreenState extends State<AddTicketScreen> {
  final _sourceController = TextEditingController();
  final _destinationController = TextEditingController();
  final _ticketNumberController = TextEditingController();
  final _qrPayloadController = TextEditingController();
  final _operatorController = TextEditingController();
  final _api = ApiService();

  String _mode = 'other';
  Uint8List? _imageBytes;
  String? _imageFilename;
  String? _uploadedImageUrl;
  int? _jobId;
  bool _isScanning = false;
  bool _isSaving = false;
  List<Map<String, dynamic>>? _transitMap;
  final List<String> _liveTail = [];
  String? _error;
  StreamSubscription<Map<String, dynamic>>? _eventsSub;

  static const _modes = ['rail', 'metro', 'bus', 'cab', 'other'];

  @override
  void dispose() {
    _eventsSub?.cancel();
    _sourceController.dispose();
    _destinationController.dispose();
    _ticketNumberController.dispose();
    _qrPayloadController.dispose();
    _operatorController.dispose();
    super.dispose();
  }

  Future<void> _ensureAuth() async {
    final authService = AuthService(_api);  // ✅ Use _api, not new instance
    final isLoggedIn = await authService.ensureAuthLoaded();
    if (!isLoggedIn) {
      return;
    }
  }

  Color _modeColor(String mode) {
    final hex = PlatformColors.forMode(mode).replaceFirst('#', '');
    return Color(int.parse('FF$hex', radix: 16));
  }

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: source, imageQuality: 85);
    if (pickedFile == null) return;

    final bytes = await pickedFile.readAsBytes();
    final name = pickedFile.name.isNotEmpty
        ? pickedFile.name
        : 'ticket_${DateTime.now().millisecondsSinceEpoch}.jpg';

    setState(() {
      _imageBytes = bytes;
      _imageFilename = name;
      _isScanning = true;
      _error = null;
      _liveTail.clear();
      _transitMap = null;
      _jobId = null;
      _uploadedImageUrl = null;
    });

    await _uploadAndTail();
  }

  Future<void> _uploadAndTail() async {
    if (_imageBytes == null || _imageFilename == null) return;

    try {
      await _ensureAuth();
      setState(() => _liveTail.add('Uploading ticket image…'));

      final upload = await _api.uploadTicketImageBytes(
        bytes: _imageBytes!,
        filename: _imageFilename!,
      );
      setState(() {
        _jobId = upload.jobId;
        _uploadedImageUrl = upload.imageUrl;
        _liveTail.add('Uploaded (job #${upload.jobId})');
      });

      await _eventsSub?.cancel();
      _eventsSub = _api
          .streamTicketJobEvents(upload.jobId)
          .listen(
            _onLiveEvent,
            onError: (Object e) {
              if (!mounted) return;
              setState(() {
                _error = e.toString();
                _isScanning = false;
                _liveTail.add('Live tail error: $e');
              });
              _pollJobFallback(upload.jobId);
            },
            onDone: () {
              if (!mounted) return;
              if (_isScanning) {
                _pollJobFallback(upload.jobId);
              }
            },
          );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isScanning = false;
        _liveTail.add('Upload failed: $e');
      });
    }
  }

  String? _usable(String? value) {
    if (value == null) return null;
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    final lower = trimmed.toLowerCase();
    if (trimmed.startsWith('<') && trimmed.endsWith('>')) return null;
    if (['station', '<station>', 'unknown', 'n/a', 'none'].contains(lower)) {
      return null;
    }
    return trimmed;
  }

  void _applyExtracted(Map<String, dynamic> data) {
    final source = _usable(data['source']?.toString());
    final destination = _usable(data['destination']?.toString());
    final ticketNumber = _usable(data['ticket_number']?.toString());
    final qr = _usable(data['qr_payload']?.toString());
    final operator = _usable(data['operator']?.toString());
    final mode = data['mode']?.toString().toLowerCase();

    if (source != null) _sourceController.text = source;
    if (destination != null) _destinationController.text = destination;
    if (ticketNumber != null) _ticketNumberController.text = ticketNumber;
    if (qr != null) _qrPayloadController.text = qr;
    if (operator != null) _operatorController.text = operator;
    if (mode != null && _modes.contains(mode)) _mode = mode;

    if (_usable(_sourceController.text) != null &&
        _usable(_destinationController.text) != null) {
      _generateTextMap(_sourceController.text, _destinationController.text);
    }
  }

  void _onLiveEvent(Map<String, dynamic> event) {
    if (!mounted) return;
    final name = event['event']?.toString() ?? 'event';
    final message = event['message']?.toString();
    setState(() {
      _liveTail.add(message != null ? '[$name] $message' : '[$name]');
    });

    if (name == 'extracted' || name == 'ready' || name == 'qr_decoded') {
      setState(() {
        _applyExtracted(event);
        if (name != 'qr_decoded') _isScanning = false;
      });
    }

    if (name == 'error') {
      setState(() {
        _isScanning = false;
        _error = event['message']?.toString() ?? 'Extraction failed';
      });
    }

    if (name == 'done' || name == 'timeout') {
      setState(() => _isScanning = false);
      if (_jobId != null &&
          (_sourceController.text.isEmpty ||
              _destinationController.text.isEmpty)) {
        _pollJobFallback(_jobId!);
      }
    }
  }

  Future<void> _pollJobFallback(int jobId) async {
    try {
      await _ensureAuth();
      final job = await _api.getTicketJob(jobId);
      if (!mounted) return;
      setState(() {
        _applyExtracted(job);
        _isScanning = false;
        _liveTail.add('Synced job status: ${job['status']}');
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isScanning = false;
        _liveTail.add('Could not sync job: $e');
      });
    }
  }

  void _generateTextMap(String src, String dest) {
    final c = _modeColor(_mode);
    setState(() {
      _transitMap = [
        {
          'id': 1,
          'label': 'Walk to $src',
          'icon': Icons.directions_walk,
          'color': Colors.amber,
        },
        {
          'id': 2,
          'label': 'Take ${_mode.toUpperCase()} toward $dest',
          'icon': Icons.train,
          'color': c,
        },
        {
          'id': 3,
          'label': 'Arrive at $dest',
          'icon': Icons.location_on,
          'color': Colors.blue,
        },
      ];
    });
  }

  void _handleManualEntry() {
    if (_sourceController.text.isNotEmpty &&
        _destinationController.text.isNotEmpty) {
      _generateTextMap(_sourceController.text, _destinationController.text);
    }
  }

  Future<void> _saveTicket() async {
    final source = _sourceController.text.trim();
    final destination = _destinationController.text.trim();
    if (source.isEmpty || destination.isEmpty) {
      setState(() => _error = 'Source and destination are required');
      return;
    }

    setState(() {
      _isSaving = true;
      _error = null;
    });

    try {
      await _ensureAuth();
      final ticketNumber = _ticketNumberController.text.trim();
      final qrPayload = _qrPayloadController.text.trim();
      final operator = _operatorController.text.trim();

      if (_jobId != null) {
        await _api.confirmTicketJob(
          jobId: _jobId!,
          source: source,
          destination: destination,
          operator: operator.isEmpty ? null : operator,
          ticketNumber: ticketNumber.isEmpty ? null : ticketNumber,
          qrPayload: qrPayload.isEmpty ? null : qrPayload,
          mode: _mode,
        );
      } else {
        await _api.addTicket(
          source: source,
          destination: destination,
          imageUrl: _uploadedImageUrl,
          ticketNumber: ticketNumber.isEmpty ? null : ticketNumber,
          qrPayload: qrPayload.isEmpty ? null : qrPayload,
          mode: _mode,
          operatorName: operator.isEmpty ? null : operator,
          sourceType: 'manual',
        );
      }

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ticket saved to Unified Wallet!')),
      );
      setState(() {
        _sourceController.clear();
        _destinationController.clear();
        _ticketNumberController.clear();
        _qrPayloadController.clear();
        _operatorController.clear();
        _imageBytes = null;
        _imageFilename = null;
        _uploadedImageUrl = null;
        _jobId = null;
        _transitMap = null;
        _liveTail.clear();
        _mode = 'other';
        _isSaving = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().contains('Already in wallet')
            ? 'Already in wallet'
            : e.toString();
        _isSaving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final accent = _modeColor(_mode);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Ticket / Pass'),
        backgroundColor: accent,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Take a photo of your physical ticket or enter it manually to add it to your wallet.',
              style: TextStyle(color: Colors.black54),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const Text(
                      'Quick Photo Scanner',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _isScanning
                                ? null
                                : () => _pickImage(ImageSource.camera),
                            icon: const Icon(Icons.camera_alt),
                            label: const Text('Camera'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _isScanning
                                ? null
                                : () => _pickImage(ImageSource.gallery),
                            icon: const Icon(Icons.photo_library),
                            label: const Text('Gallery'),
                          ),
                        ),
                      ],
                    ),
                    if (_imageBytes != null) ...[
                      const SizedBox(height: 12),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.memory(_imageBytes!, height: 160,
                            fit: BoxFit.cover),
                      ),
                    ],
                    if (_uploadedImageUrl != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          'Stored: ${ApiConfig.resolveUrl(_uploadedImageUrl!)}',
                          style: const TextStyle(
                            fontSize: 11,
                            color: Colors.grey,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    if (_isScanning || _liveTail.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.black87,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Live processing',
                                style: TextStyle(
                                    color: Colors.white70,
                                    fontWeight: FontWeight.bold)),
                            const SizedBox(height: 8),
                            ..._liveTail.map(
                              (l) => Text(l,
                                  style: const TextStyle(
                                      color: Colors.greenAccent,
                                      fontFamily: 'monospace',
                                      fontSize: 12)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 20),
              child: Center(
                child: Text(
                  'OR',
                  style: TextStyle(
                    color: Colors.grey,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const Text(
                      'Manual Entry',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _sourceController,
                      decoration: const InputDecoration(
                        labelText: 'Source Station',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _destinationController,
                      decoration: const InputDecoration(
                        labelText: 'Destination Station',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _ticketNumberController,
                      decoration: const InputDecoration(
                        labelText: 'Ticket Number / UTS / PNR',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _qrPayloadController,
                      decoration: const InputDecoration(
                        labelText: 'QR Payload (paste or from scan)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _operatorController,
                      decoration: const InputDecoration(
                        labelText: 'Operator',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      key: ValueKey(_mode),
                      initialValue: _mode,
                      decoration: const InputDecoration(
                        labelText: 'Platform',
                        border: OutlineInputBorder(),
                      ),
                      items: _modes
                          .map((m) => DropdownMenuItem(
                                value: m,
                                child: Text(m.toUpperCase()),
                              ))
                          .toList(),
                      onChanged: (v) {
                        if (v == null) return;
                        setState(() => _mode = v);
                        if (_sourceController.text.isNotEmpty &&
                            _destinationController.text.isNotEmpty) {
                          _generateTextMap(_sourceController.text,
                              _destinationController.text);
                        }
                      },
                    ),
                    const SizedBox(height: 16),
                    OutlinedButton(
                      onPressed: _handleManualEntry,
                      child: const Text('Show Route Map'),
                    ),
                  ],
                ),
              ),
            ),
            if (_transitMap != null)
              Padding(
                padding: const EdgeInsets.only(top: 24),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          'Active Transit Route',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 16),
                        ..._transitMap!.map((step) {
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 16),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  backgroundColor: step['color'] as Color,
                                  radius: 16,
                                  child: Icon(step['icon'] as IconData,
                                      size: 16, color: Colors.white),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                    child: Text(step['label'] as String,
                                        style: const TextStyle(fontSize: 16))),
                              ],
                            ),
                          );
                        }),
                        ElevatedButton(
                          onPressed: _isSaving ? null : _saveTicket,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: Text(
                            _isSaving ? 'Saving…' : 'Save to Wallet',
                            style: const TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
