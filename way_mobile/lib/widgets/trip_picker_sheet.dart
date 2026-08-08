import 'package:flutter/material.dart';

import '../models/booking.dart';
import 'create_trip_sheet.dart';

/// Result of picking a trip: either an existing trip id, or create-new payload.
class TripPickerResult {
  final int? tripId;
  final String? newName;
  final String? newNotes;
  final String? newTravelDate;

  const TripPickerResult.existing(this.tripId)
      : newName = null,
        newNotes = null,
        newTravelDate = null;

  const TripPickerResult.create({
    required this.newName,
    this.newNotes,
    this.newTravelDate,
  }) : tripId = null;

  bool get isCreate => tripId == null && newName != null;
}

Future<TripPickerResult?> showTripPickerSheet(
  BuildContext context, {
  required List<TicketTrip> trips,
}) {
  return showModalBottomSheet<TripPickerResult>(
    context: context,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => TripPickerSheet(trips: trips),
  );
}

class TripPickerSheet extends StatelessWidget {
  final List<TicketTrip> trips;

  const TripPickerSheet({super.key, required this.trips});

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 16, 16, 16 + bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Add to trip',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          ListTile(
            leading: const Icon(Icons.add_circle_outline),
            title: const Text('Create new trip'),
            onTap: () async {
              final created = await showCreateTripSheet(context);
              if (created == null) return;
              if (!context.mounted) return;
              Navigator.pop(
                context,
                TripPickerResult.create(
                  newName: created['name'],
                  newNotes: created['notes'],
                  newTravelDate: created['travelDate'],
                ),
              );
            },
          ),
          if (trips.isNotEmpty) ...[
            const Divider(),
            ConstrainedBox(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(context).size.height * 0.4,
              ),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: trips.length,
                itemBuilder: (ctx, i) {
                  final trip = trips[i];
                  return ListTile(
                    leading: const Icon(Icons.folder_outlined),
                    title: Text(trip.name),
                    subtitle: Text(
                      '${trip.ticketCount} ticket${trip.ticketCount == 1 ? '' : 's'}'
                      '${trip.travelDate != null ? ' · ${trip.travelDate}' : ''}',
                    ),
                    onTap: () =>
                        Navigator.pop(context, TripPickerResult.existing(trip.id)),
                  );
                },
              ),
            ),
          ] else
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Text(
                'No trips yet — create one to group tickets.',
                style: TextStyle(color: Colors.grey.shade600),
                textAlign: TextAlign.center,
              ),
            ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}
