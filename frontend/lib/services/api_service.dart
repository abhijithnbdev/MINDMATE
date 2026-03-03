import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../core/constants/api_constants.dart';

class ApiService {
  // 1. Upload Audio (Voice Mode)
  static Future<Map<String, dynamic>> uploadAudio(String userId, File audioFile) async {
    var uri = Uri.parse("${ApiConstants.baseUrl}/chat/upload-audio");
    var request = http.MultipartRequest('POST', uri);

    request.fields['user_id'] = userId;
    request.files.add(await http.MultipartFile.fromPath(
      'file',
      audioFile.path,
      contentType: MediaType('audio', 'm4a'),
    ));

    try {
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        return {"transcript": "Error: ${response.statusCode}", "ai_response": "Server error."};
      }
    } catch (e) {
      return {"transcript": "Connection Error", "ai_response": "Could not connect to backend."};
    }
  }

  // 2. Get Memories (Timeline)
  static Future<List<dynamic>> getMemories(String userId, {String? category}) async {
    final query = category != null && category.isNotEmpty 
      ? 'user_id=$userId&category=$category' 
      : 'user_id=$userId';
    final url = Uri.parse('${ApiConstants.memories}?$query');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['timeline'] ?? [];
      }
    } catch (e) {
      print("Error fetching memories: $e");
    }
    return [];
  }

  // 3. Add Memory (Manual Entry)
  static Future<bool> addMemory(String userId, String title, String content, String category) async {
    final url = Uri.parse('${ApiConstants.baseUrl}/memories');
    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: json.encode({
          "user_id": userId,
          "title": title,
          "content": content,
          "category": category,
          "type": "note" // Default type
        }),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("Error adding memory: $e");
      return false;
    }
  }

  // 4. Get Chat History
  static Future<List<dynamic>> getChatHistory(String userId) async {
    final url = Uri.parse('${ApiConstants.baseUrl}/chat/history?user_id=$userId');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['messages'] ?? [];
      }
    } catch (e) {
      print("Error fetching chat: $e");
    }
    return [];
  }
  static Future<Map<String, dynamic>> generateSchedule(String date) async {
    final url = Uri.parse('${ApiConstants.predictScheduleEndpoint}?date=$date'); 
    
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print("Error generating schedule: $e");
    }
    return {};
  }

}

