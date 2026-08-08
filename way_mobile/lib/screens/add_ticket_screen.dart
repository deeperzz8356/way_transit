import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../services/api_service.dart';

class AddTicketScreen extends StatefulWidget {
  const AddTicketScreen({super.key});

  @override
  State<AddTicketScreen> createState() => _AddTicketScreenState();
}

class _AddTicketScreenState extends State<AddTicketScreen> {
  final _sourceController = TextEditingController();
  final _destinationController = TextEditingController();
  final _api = ApiService();
  String? _error;
  StreamSubscription<Map<String, dynamic>>? _eventsSub;

  @override
  void dispose() {
    _eventsSub?.cancel();
    _sourceController.dispose();
    _destinationController.dispose();
    super.dispose();
  }

  Future<void> _ensureAuth() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    _api.setToken(token ?? 'dev-token');
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
      setState(() {
        _liveTail.add('Uploading ticket image…');
      });

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

  String? _usableStation(String? value) {
    if (value == null) return null;
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    final lower = trimmed.toLowerCase();
    if (trimmed.startsWith('<') && trimmed.endsWith('>')) return null;
    if (lower == 'station' ||
        lower == '<station>' ||
        lower == 'unknown' ||
        lower == 'n/a' ||
        lower == 'none') {
      return null;
    }
    return trimmed;
  }

  void _onLiveEvent(Map<String, dynamic> event) {
    if (!mounted) return;
    final name = event['event']?.toString() ?? 'event';
    final message = event['message']?.toString();
    setState(() {
      _liveTail.add(message != null ? '[$name] $message' : '[$name]');
    });

    if (name == 'extracted' || name == 'ready') {
      final source = _usableStation(event['source']?.toString());
      final destination = _usableStation(event['destination']?.toString());
      if (source != null) {
        _sourceController.text = source;
      }
      if (destination != null) {
        _destinationController.text = destination;
      }
      if (_sourceController.text.isNotEmpty &&
          _destinationController.text.isNotEmpty &&
          _usableStation(_sourceController.text) != null &&
          _usableStation(_destinationController.text) != null) {
        _generateTextMap(_sourceController.text, _destinationController.text);
      }
      setState(() => _isScanning = false);
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
      final source = _usableStation(job['source']?.toString());
      final destination = _usableStation(job['destination']?.toString());
      setState(() {
        if (source != null) {
          _sourceController.text = source;
        }
        if (destination != null) {
          _destinationController.text = destination;
        }
        _isScanning = false;
        _liveTail.add('Synced job status: ${job['status']}');
      });
      if (_usableStation(_sourceController.text) != null &&
          _usableStation(_destinationController.text) != null) {
        _generateTextMap(_sourceController.text, _destinationController.text);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isScanning = false;
        _liveTail.add('Could not sync job: $e');
      });
    }
  }

  void _generateTextMap(String src, String dest) {
    setState(() {
      _transitMap = [
        {
          'id': 1,
          'type': 'walk',
          'label': 'Walk to $src',
          'icon': Icons.directions_walk,
          'color': Colors.amber,
        },
        {
          'id': 2,
          'type': 'transit',
          'label': 'Take transit toward $dest',
          'icon': Icons.train,
          'color': Colors.red,
        },
        {
          'id': 3,
          'type': 'transit',
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
      if (_jobId != null) {
        await _api.confirmTicketJob(
          jobId: _jobId!,
          source: source,
          destination: destination,
        );
      } else {
        await _api.addTicket(
          source: source,
          destination: destination,
          imageUrl: _uploadedImageUrl,
        );
      }

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ticket saved to Unified Wallet!')),
      );
      setState(() {
        _sourceController.clear();
        _destinationController.clear();
        _imageBytes = null;
        _imageFilename = null;
        _uploadedImageUrl = null;
        _jobId = null;
        _transitMap = null;
        _liveTail.clear();
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Ticket / Pass')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Take a photo of your physical ticket or enter it manually to add it to your wallet.',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 24),
            if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.red[100],
                margin: const EdgeInsets.only(bottom: 16),
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            Card(
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
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
                          child: ElevatedButton.icon(
                            onPressed: _isScanning
                                ? null
                                : () => _pickImage(ImageSource.camera),
                            icon: const Icon(Icons.camera_alt),
                            label: const Text('Camera'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: _isScanning
                                ? null
                                : () => _pickImage(ImageSource.gallery),
                            icon: const Icon(Icons.photo_library),
                            label: const Text('Gallery'),
                          ),
                        ),
                      ],
                    ),
                    if (_isScanning)
                      const Padding(
                        padding: EdgeInsets.only(top: 16.0),
                        child: Column(
                          children: [
                            CircularProgressIndicator(),
                            SizedBox(height: 8),
                            Text(
                              'Processing ticket…',
                              style: TextStyle(
                                fontStyle: FontStyle.italic,
                                color: Colors.orange,
                              ),
                            ),
                          ],
                        ),
                      ),
                    if (_imageBytes != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 16.0),
                        child: Image.memory(
                          _imageBytes!,
                          height: 150,
                          fit: BoxFit.cover,
                        ),
                      ),
                    if (_uploadedImageUrl != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8.0),
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
                    if (_liveTail.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          'Live processing',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        constraints: const BoxConstraints(maxHeight: 160),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF111827),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: ListView.builder(
                          shrinkWrap: true,
                          itemCount: _liveTail.length,
                          itemBuilder: (context, index) {
                            return Text(
                              _liveTail[index],
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 12,
                                color: Color(0xFFD1FAE5),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24.0),
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
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
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
                    const SizedBox(height: 16),
                    TextField(
                      controller: _destinationController,
                      decoration: const InputDecoration(
                        labelText: 'Destination Station',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _handleManualEntry,
                      child: const Text('Show Route Map'),
                    ),
                  ],
                ),
              ),
            ),
            if (_transitMap != null)
              Padding(
                padding: const EdgeInsets.only(top: 24.0),
                child: Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
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
                            padding: const EdgeInsets.only(bottom: 16.0),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  backgroundColor: step['color'] as Color,
                                  radius: 16,
                                  child: Icon(
                                    step['icon'] as IconData,
                                    size: 16,
                                    color: Colors.white,
                                  ),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Text(
                                    step['label'] as String,
                                    style: const TextStyle(fontSize: 16),
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),
                        const SizedBox(height: 16),
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
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
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
