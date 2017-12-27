# Database Project
## PriCoSha

A system that allows users to share content items (links to images) either:
1. Publicly (visible to all users)
2. Privately (to a group of people called a FriendGroup)

FriendGroups have one owner and at least 2 other members. The owner is the only person who could remove or add someone to the group. An owner cannot create another group with the same name. However, an owner can be part of a group that has an identical name.

For example, Ann can create a FriendGroup called "Friends". She cannot create another group called "Friends" and be the owner of it.
However, it is acceptable if David creates a FriendGroup called "Friends" and adds Ann to it.

Users are able to view posts, comment, or tag others based on the post's visibility. If a post is shared in a FriendGroup and the user is in the group, they are able to tag people in the same group, comment, and view the post. If a post is public, anyone can view, comment, or tag the post.

If userA tags userB, then userB must approve the tag before their name is visible on the post. UserB has to option to approve the tag, deny the tag, or leave it as pending. UserA would not know about userB's choice other than the tag being approved. 

--------------------------------------------------------
Nathan Ly

Anish Malhotra
