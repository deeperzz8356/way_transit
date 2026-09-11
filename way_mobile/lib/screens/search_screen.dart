// screens/search_screen.dart
// Source → Destination transit search screen.
// Works on Flutter Web, Android, iOS, and desktop.

import 'dart:async';
import 'package:flutter/material.dart';
import '../models/transit_search.dart';
import '../services/api_service.dart';

// ── Design tokens ─────────────────────────────────────────────────────────────
const _kPrimary = Color(0xFF5974FF);
const _kBg      = Color(0xFFF8F9FE);
const _kCard    = Colors.white;
const _kLabel   = Color(0xFF1A1B35);
const _kHint    = Color(0xFF8C90A3);
const _kDivider = Color(0xFFEEEFF4);

enum _ActiveField { none, source, destination }

// ── SearchScreen ──────────────────────────────────────────────────────────────
class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _api = ApiService();

  // Source
  final _srcCtrl  = TextEditingController();
  final _srcFocus = FocusNode();
  StopResult?      _srcStop;
  List<StopResult> _srcSuggestions = [];
  bool             _srcLoading     = false;
  Timer?           _srcDebounce;

  // Destination
  final _dstCtrl  = TextEditingController();
  final _dstFocus = FocusNode();
  StopResult?      _dstStop;
  List<StopResult> _dstSuggestions = [];
  bool             _dstLoading     = false;
  Timer?           _dstDebounce;

  // Dropdown state
  _ActiveField _active = _ActiveField.none;

  // Results
  List<TripSearchResult> _results       = [];
  bool                   _searching     = false;
  String?                _searchMessage;
  bool                   _hasSearched   = false;

  // Key for measuring panel height (for dropdown positioning)
  final _panelKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    // Listen to controllers so the button reacts on EVERY keystroke,
    // including Flutter Web where onChanged can be unreliable.
    _srcCtrl.addListener(_onControllerChange);
    _dstCtrl.addListener(_onControllerChange);
    _srcFocus.addListener(_onSrcFocusChange);
    _dstFocus.addListener(_onDstFocusChange);
  }

  // Called whenever either controller changes — forces a rebuild so
  // _canSearch re-evaluates and the button enables/disables correctly.
  void _onControllerChange() {
    if (mounted) setState(() {});
  }

  void _onSrcFocusChange() {
    if (!_srcFocus.hasFocus && _active == _ActiveField.source) {
      Future.delayed(const Duration(milliseconds: 180), () {
        if (mounted && _active == _ActiveField.source) {
          setState(() => _active = _ActiveField.none);
        }
      });
    }
  }

  void _onDstFocusChange() {
    if (!_dstFocus.hasFocus && _active == _ActiveField.destination) {
      Future.delayed(const Duration(milliseconds: 180), () {
        if (mounted && _active == _ActiveField.destination) {
          setState(() => _active = _ActiveField.none);
        }
      });
    }
  }

  @override
  void dispose() {
    _srcCtrl.removeListener(_onControllerChange);
    _dstCtrl.removeListener(_onControllerChange);
    _srcCtrl.dispose();
    _srcFocus.removeListener(_onSrcFocusChange);
    _srcFocus.dispose();
    _dstCtrl.removeListener(_onControllerChange);
    _dstCtrl.dispose();
    _dstFocus.removeListener(_onDstFocusChange);
    _dstFocus.dispose();
    _srcDebounce?.cancel();
    _dstDebounce?.cancel();
    super.dispose();
  }

  // ── Autocomplete ────────────────────────────────────────────────────────────

  void _onSrcChanged(String val) {
    // Clear the resolved stop whenever the user edits the field
    if (_srcStop != null) setState(() => _srcStop = null);
    _srcDebounce?.cancel();
    if (val.trim().length < 2) {
      setState(() { _srcSuggestions = []; _active = _ActiveField.none; });
      return;
    }
    _srcDebounce = Timer(
      const Duration(milliseconds: 350),
      () => _fetchStops(val, isSrc: true),
    );
  }

  void _onDstChanged(String val) {
    if (_dstStop != null) setState(() => _dstStop = null);
    _dstDebounce?.cancel();
    if (val.trim().length < 2) {
      setState(() { _dstSuggestions = []; _active = _ActiveField.none; });
      return;
    }
    _dstDebounce = Timer(
      const Duration(milliseconds: 350),
      () => _fetchStops(val, isSrc: false),
    );
  }

  Future<void> _fetchStops(String q, {required bool isSrc}) async {
    if (!mounted) return;
    setState(() { if (isSrc) _srcLoading = true; else _dstLoading = true; });
    try {
      final raw = await _api.searchStops(q);
      if (!mounted) return;
      final stops = raw.map(StopResult.fromJson).toList();
      setState(() {
        if (isSrc) {
          _srcSuggestions = stops;
          _active = stops.isNotEmpty ? _ActiveField.source : _ActiveField.none;
        } else {
          _dstSuggestions = stops;
          _active = stops.isNotEmpty ? _ActiveField.destination : _ActiveField.none;
        }
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        if (isSrc) _srcSuggestions = []; else _dstSuggestions = [];
        _active = _ActiveField.none;
      });
    } finally {
      if (mounted) setState(() { if (isSrc) _srcLoading = false; else _dstLoading = false; });
    }
  }

  void _pickSrc(StopResult s) {
    setState(() {
      _srcStop = s;
      _srcCtrl.text = s.name;
      _srcSuggestions = [];
      _active = _ActiveField.none;
    });
    _srcFocus.unfocus();
    // Move focus to destination so the user can fill it next
    Future.delayed(const Duration(milliseconds: 50), () {
      if (mounted && _dstCtrl.text.trim().isEmpty) {
        _dstFocus.requestFocus();
      }
    });
  }

  void _pickDst(StopResult s) {
    setState(() {
      _dstStop = s;
      _dstCtrl.text = s.name;
      _dstSuggestions = [];
      _active = _ActiveField.none;
    });
    _dstFocus.unfocus();
  }

  void _clearSrc() {
    setState(() {
      _srcStop = null; _srcCtrl.clear();
      _srcSuggestions = []; _active = _ActiveField.none;
    });
  }

  void _clearDst() {
    setState(() {
      _dstStop = null; _dstCtrl.clear();
      _dstSuggestions = []; _active = _ActiveField.none;
    });
  }

  void _swap() {
    setState(() {
      final tmpStop = _srcStop; final tmpText = _srcCtrl.text;
      _srcStop = _dstStop;  _srcCtrl.text = _dstCtrl.text;
      _dstStop = tmpStop;   _dstCtrl.text = tmpText;
      _srcSuggestions = []; _dstSuggestions = [];
      _active = _ActiveField.none;
      _results = []; _searchMessage = null; _hasSearched = false;
    });
  }

  void _dismissDropdown() {
    if (_active != _ActiveField.none) setState(() => _active = _ActiveField.none);
  }

  // ── Search ──────────────────────────────────────────────────────────────────

  // Enabled whenever both fields have at least 2 characters.
  // The user does NOT need to tap a suggestion — typing and pressing Search
  // will auto-resolve to the best matching stop.
  bool get _canSearch =>
      _srcCtrl.text.trim().length >= 2 &&
      _dstCtrl.text.trim().length >= 2 &&
      !_searching;

  // Resolve a typed name to a StopResult via the API.
  Future<StopResult> _resolveText(String text) async {
    final q = text.trim();
    final raw = await _api.searchStops(q);
    if (raw.isEmpty) {
      throw Exception('No stop found for "$q". Try a different name.');
    }
    final stops = raw.map(StopResult.fromJson).toList();
    // Prefer exact name match, otherwise take the first (best-ranked) result
    return stops.firstWhere(
      (s) => s.name.toLowerCase() == q.toLowerCase(),
      orElse: () => stops.first,
    );
  }

  Future<void> _search() async {
    if (!_canSearch) return;
    _dismissDropdown();
    FocusScope.of(context).unfocus();

    setState(() {
      _searching = true;
      _results = [];
      _searchMessage = null;
      _hasSearched = true;
    });

    try {
      // Resolve source if user typed but didn't pick from dropdown
      if (_srcStop == null) {
        final s = await _resolveText(_srcCtrl.text);
        if (!mounted) return;
        setState(() { _srcStop = s; _srcCtrl.text = s.name; });
      }

      // Resolve destination if user typed but didn't pick from dropdown
      if (_dstStop == null) {
        final s = await _resolveText(_dstCtrl.text);
        if (!mounted) return;
        setState(() { _dstStop = s; _dstCtrl.text = s.name; });
      }

      if (_srcStop!.id == _dstStop!.id) {
        setState(() {
          _searchMessage = 'Source and destination cannot be the same stop.';
          _hasSearched = true;
        });
        return;
      }

      final raw = await _api.searchTrips(
        sourceStopId: _srcStop!.id,
        destinationStopId: _dstStop!.id,
      );
      if (!mounted) return;
      final list = raw['results'] as List? ?? [];
      setState(() {
        _results = list
            .map((e) => TripSearchResult.fromJson(e as Map<String, dynamic>))
            .toList();
        _searchMessage = raw['message'] as String? ?? '';
      });
    } on Exception catch (e) {
      if (!mounted) return;
      setState(() => _searchMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _searching = false);
    }
  }

  void _snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(msg), backgroundColor: Colors.red.shade700,
             behavior: SnackBarBehavior.floating),
  );

  // ── Build ────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final showDropdown = _active != _ActiveField.none;
    final dropdownItems = _active == _ActiveField.source
        ? _srcSuggestions : _dstSuggestions;
    final onDropdownPick = _active == _ActiveField.source ? _pickSrc : _pickDst;

    return Scaffold(
      backgroundColor: _kBg,
      appBar: AppBar(
        backgroundColor: _kCard,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 18, color: _kLabel),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Find Services',
          style: TextStyle(color: _kLabel, fontWeight: FontWeight.bold, fontSize: 18)),
        centerTitle: true,
      ),
      body: GestureDetector(
        behavior: HitTestBehavior.translucent,
        onTap: () { FocusScope.of(context).unfocus(); _dismissDropdown(); },
        child: Stack(
          children: [
            // Layer 0 — panel + results
            Column(
              children: [
                Material(
                  key: _panelKey,
                  color: _kCard,
                  elevation: 2,
                  child: _buildPanel(),
                ),
                Expanded(child: _buildBody()),
              ],
            ),

            // Layer 1 — floating dropdown (only when suggestions exist)
            if (showDropdown && dropdownItems.isNotEmpty)
              _FloatingDropdown(
                panelKey: _panelKey,
                items: dropdownItems,
                onPick: onDropdownPick,
              ),
          ],
        ),
      ),
    );
  }

  // ── Search panel ─────────────────────────────────────────────────────────────

  Widget _buildPanel() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Source field
          _StopInputField(
            controller: _srcCtrl,
            focusNode:  _srcFocus,
            hint:       'From — e.g. Thane',
            icon:       Icons.trip_origin_rounded,
            dotColor:   const Color(0xFF22C55E),
            loading:    _srcLoading,
            resolved:   _srcStop != null,
            onChanged:  _onSrcChanged,
            onClear:    _clearSrc,
            onSubmitted: (_) {
              if (_dstCtrl.text.trim().isEmpty) _dstFocus.requestFocus();
              else if (_canSearch) _search();
            },
          ),

          // Swap button row
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: _swap,
              icon:  const Icon(Icons.swap_vert, size: 18),
              label: const Text('Swap', style: TextStyle(fontSize: 12)),
              style: TextButton.styleFrom(
                foregroundColor: _kPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              ),
            ),
          ),

          // Destination field
          _StopInputField(
            controller: _dstCtrl,
            focusNode:  _dstFocus,
            hint:       'To — e.g. Panvel',
            icon:       Icons.location_on_rounded,
            dotColor:   const Color(0xFFEF4444),
            loading:    _dstLoading,
            resolved:   _dstStop != null,
            onChanged:  _onDstChanged,
            onClear:    _clearDst,
            onSubmitted: (_) { if (_canSearch) _search(); },
          ),

          const SizedBox(height: 14),

          // Search button — always tappable; resolves typed text on press
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _canSearch ? _search : null,
              icon: _searching
                  ? const SizedBox(
                      width: 18, height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.search, size: 20),
              label: Text(_searching ? 'Searching…' : 'Search'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _kPrimary,
                disabledBackgroundColor: _kPrimary.withValues(alpha: 0.35),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
                elevation: 0,
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Body states ───────────────────────────────────────────────────────────────

  Widget _buildBody() {
    if (_searching)      return const Center(child: CircularProgressIndicator());
    if (!_hasSearched)   return _buildEmptyState();
    if (_results.isEmpty) return _buildNoResults();
    return _buildResults();
  }

  Widget _buildEmptyState() => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.train_rounded, size: 64, color: _kPrimary.withValues(alpha: 0.25)),
        const SizedBox(height: 16),
        const Text(
          'Type source and destination above,\nthen tap Search.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 15, color: _kHint),
        ),
      ],
    ),
  );

  Widget _buildNoResults() => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.search_off_rounded, size: 56, color: Colors.grey.shade400),
          const SizedBox(height: 16),
          Text(
            _searchMessage ?? 'No direct service found between the selected stops.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 15, color: Colors.grey.shade600),
          ),
        ],
      ),
    ),
  );

  Widget _buildResults() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 6),
          child: Row(
            children: [
              Text(
                '${_results.length} service${_results.length == 1 ? '' : 's'} found',
                style: const TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600, color: _kHint),
              ),
              const Spacer(),
              if (_srcStop != null && _dstStop != null)
                Flexible(
                  child: Text(
                    '${_srcStop!.name} → ${_dstStop!.name}',
                    style: const TextStyle(
                        fontSize: 12, color: _kPrimary, fontWeight: FontWeight.w600),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
            itemCount: _results.length,
            itemBuilder: (_, i) => _TripCard(trip: _results[i]),
          ),
        ),
      ],
    );
  }
}

// ── _StopInputField ───────────────────────────────────────────────────────────
// Stateless input field. Using a separate widget ensures the TextField
// rebuild is isolated and onChanged fires correctly on all platforms.

class _StopInputField extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final String hint;
  final IconData icon;
  final Color dotColor;
  final bool loading;
  final bool resolved;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;
  final ValueChanged<String>? onSubmitted;

  const _StopInputField({
    required this.controller,
    required this.focusNode,
    required this.hint,
    required this.icon,
    required this.dotColor,
    required this.loading,
    required this.resolved,
    required this.onChanged,
    required this.onClear,
    this.onSubmitted,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF4F6FB),
        borderRadius: BorderRadius.circular(14),
        border: resolved
            ? Border.all(color: _kPrimary.withValues(alpha: 0.6), width: 1.5)
            : Border.all(color: Colors.transparent, width: 1.5),
      ),
      child: TextField(
        controller: controller,
        focusNode:  focusNode,
        onChanged:  onChanged,
        onSubmitted: onSubmitted,
        textInputAction: TextInputAction.next,
        style: const TextStyle(fontSize: 15, color: _kLabel),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: const TextStyle(color: _kHint, fontSize: 14),
          prefixIcon: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 10, height: 10,
                  decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
                ),
                const SizedBox(width: 8),
                Icon(icon, color: dotColor, size: 18),
              ],
            ),
          ),
          prefixIconConstraints: const BoxConstraints(minWidth: 0, minHeight: 0),
          suffixIcon: loading
              ? const Padding(
                  padding: EdgeInsets.all(12),
                  child: SizedBox(
                    width: 16, height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              : controller.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.close, size: 18, color: _kHint),
                      onPressed: onClear,
                    )
                  : null,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
        ),
      ),
    );
  }
}

// ── _FloatingDropdown ─────────────────────────────────────────────────────────

class _FloatingDropdown extends StatefulWidget {
  final GlobalKey panelKey;
  final List<StopResult> items;
  final ValueChanged<StopResult> onPick;

  const _FloatingDropdown({
    required this.panelKey,
    required this.items,
    required this.onPick,
  });

  @override
  State<_FloatingDropdown> createState() => _FloatingDropdownState();
}

class _FloatingDropdownState extends State<_FloatingDropdown> {
  double _top = 180; // safe default until measured

  @override
  void initState() {
    super.initState();
    _measure();
  }

  @override
  void didUpdateWidget(_FloatingDropdown old) {
    super.didUpdateWidget(old);
    _measure();
  }

  void _measure() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final box = widget.panelKey.currentContext?.findRenderObject() as RenderBox?;
      if (box != null && box.size.height > 0) {
        final h = box.size.height;
        if (h != _top) setState(() => _top = h);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: _top + 2,
      left: 16,
      right: 16,
      child: Material(
        elevation: 8,
        borderRadius: BorderRadius.circular(12),
        shadowColor: Colors.black26,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxHeight: 260),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: ListView.separated(
              padding: EdgeInsets.zero,
              shrinkWrap: true,
              itemCount: widget.items.length,
              separatorBuilder: (_, __) => const Divider(height: 1, color: _kDivider),
              itemBuilder: (_, i) {
                final s = widget.items[i];
                return InkWell(
                  onTap: () => widget.onPick(s),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                    child: Row(
                      children: [
                        Icon(_modeIcon(s.mode), size: 17, color: _modeColor(s.mode)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(s.name,
                            style: const TextStyle(
                              fontSize: 14, fontWeight: FontWeight.w500, color: _kLabel),
                            overflow: TextOverflow.ellipsis),
                        ),
                        if (s.mode != null) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                            decoration: BoxDecoration(
                              color: _modeColor(s.mode).withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(s.mode!.toUpperCase(),
                              style: TextStyle(
                                fontSize: 10, fontWeight: FontWeight.w700,
                                color: _modeColor(s.mode), letterSpacing: 0.4)),
                          ),
                        ],
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

// ── Mode helpers ──────────────────────────────────────────────────────────────

IconData _modeIcon(String? mode) {
  switch ((mode ?? '').toLowerCase()) {
    case 'train': case 'rail':   return Icons.train;
    case 'metro': case 'subway': return Icons.subway;
    case 'bus':                  return Icons.directions_bus;
    default:                     return Icons.directions_transit;
  }
}

Color _modeColor(String? mode) {
  switch ((mode ?? '').toLowerCase()) {
    case 'train': case 'rail':   return const Color(0xFFB45309);
    case 'metro': case 'subway': return const Color(0xFF7C3AED);
    case 'bus':                  return const Color(0xFFDC2626);
    default:                     return _kHint;
  }
}

// ── _TripCard ─────────────────────────────────────────────────────────────────

class _TripCard extends StatelessWidget {
  final TripSearchResult trip;
  const _TripCard({required this.trip});

  @override
  Widget build(BuildContext context) {
    Color modeColor;
    try {
      modeColor = Color(
        int.parse('FF${trip.modeColorHex.replaceFirst('#', '')}', radix: 16));
    } catch (_) {
      modeColor = _kHint;
    }

    final IconData modeIcon;
    switch (trip.mode.toLowerCase()) {
      case 'metro': case 'subway': modeIcon = Icons.subway_rounded; break;
      case 'bus':                  modeIcon = Icons.directions_bus_rounded; break;
      default:                     modeIcon = Icons.train_rounded;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: _kCard,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10, offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Expanded(
                  child: Text(trip.displayName,
                    style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w700, color: _kLabel),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: modeColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(trip.mode.toUpperCase(),
                    style: TextStyle(
                      fontSize: 11, fontWeight: FontWeight.bold, color: modeColor)),
                ),
              ],
            ),

            const SizedBox(height: 14),

            // Journey timeline
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Departure
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(trip.departureTimeDisplay,
                        style: const TextStyle(
                          fontSize: 22, fontWeight: FontWeight.bold, color: _kLabel)),
                      const SizedBox(height: 2),
                      Text(trip.source.name,
                        style: const TextStyle(fontSize: 12, color: _kHint),
                        maxLines: 1, overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),

                // Line + duration
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 6),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          _dot(modeColor), _line(modeColor),
                          Icon(modeIcon, size: 16, color: modeColor),
                          _line(modeColor), _dot(modeColor),
                        ],
                      ),
                      if (trip.durationDisplay.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 3),
                          child: Text(trip.durationDisplay,
                            style: TextStyle(
                              fontSize: 11, color: modeColor,
                              fontWeight: FontWeight.w600)),
                        ),
                    ],
                  ),
                ),

                // Arrival
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(trip.arrivalTimeDisplay,
                        style: const TextStyle(
                          fontSize: 22, fontWeight: FontWeight.bold, color: _kLabel)),
                      const SizedBox(height: 2),
                      Text(trip.destination.name,
                        style: const TextStyle(fontSize: 12, color: _kHint),
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.end),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Footer
            Row(
              children: [
                const Icon(Icons.route_rounded, size: 13, color: _kHint),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(trip.routeName,
                    style: const TextStyle(fontSize: 12, color: _kHint),
                    overflow: TextOverflow.ellipsis),
                ),
                if (trip.direction.isNotEmpty) ...[
                  const SizedBox(width: 6),
                  _badge(trip.direction, modeColor),
                ],
                if (trip.operatorName != null && trip.operatorName!.isNotEmpty) ...[
                  const SizedBox(width: 6),
                  _badge(trip.operatorName!, modeColor),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _dot(Color c)  => Container(
    width: 6, height: 6,
    decoration: BoxDecoration(color: c, shape: BoxShape.circle));

  Widget _line(Color c) => Container(
    width: 30, height: 2, color: c.withValues(alpha: 0.35));

  Widget _badge(String label, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.1),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Text(label,
      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color)),
  );
}
